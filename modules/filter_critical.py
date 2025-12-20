"""
filter_critical.py - CRITICAL抽出モジュール（pandas版）

責務:
- severity_extracted/*.csv から Severity=CRITICAL の行のみを抽出
- ファイルごとに個別処理（マージしない）
- critical_only/*.csv に出力
- 内部的にpandasで高速処理

処理フロー:
    1. 各CSVファイルから Severity=CRITICAL の行をフィルタ
    2. ファイルごとに個別のCSVとして出力（マージしない）
    3. 80万行分割を維持

列構造:
    入力/出力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, protocol, SeverityLevel, Severity, Message]
"""

from pathlib import Path
from typing import List, Union
import pandas as pd


class FilterCriticalError(Exception):
    """CRITICAL抽出処理のカスタム例外"""

    pass


def filter_critical(
    input_files: List[Path],
    output_dir: Union[str, Path],
    severity_filter: str = "CRITICAL",
    verbose: bool = True,
) -> List[Path]:
    """
    指定されたSeverityの行のみを抽出（ファイルごと個別処理）

    各CSVファイルからSeverity列が指定された値の行のみを抽出し、
    ファイルごとに個別のCSVファイルとして出力する。
    マージは行わず、80万行分割を維持する。

    内部的にpandasで処理し、高速化を実現。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        severity_filter: フィルタするSeverity値（デフォルト: "CRITICAL"）
        verbose: 詳細ログを出力するか

    Returns:
        List[Path]: 出力されたCSVファイルのPathリスト（CRITICAL行があるファイルのみ）

    Raises:
        FilterCriticalError: CRITICAL抽出処理に失敗した場合

    Examples:
        >>> output_files = filter_critical(csv_files, "critical_only")
        >>> output_files = filter_critical(csv_files, "warning_only", severity_filter="WARNING")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_files:
        if verbose:
            print("⚠️  入力ファイルがありません")
        return []

    try:
        output_files = []
        total_rows = 0
        critical_rows = 0

        for input_path in input_files:
            # pandasでCSVを読み込み
            df = pd.read_csv(input_path, encoding="utf-8", keep_default_na=False)

            # Severity列の存在確認
            if "Severity" not in df.columns:
                raise FilterCriticalError(
                    f"Severity列が見つかりません: {input_path.name}"
                )

            total_rows += len(df)

            # 指定されたSeverityの行のみフィルタ
            critical_df = df[df["Severity"] == severity_filter]

            # CRITICAL行がある場合のみファイル出力
            if len(critical_df) > 0:
                # 出力ファイル名を生成（入力と同じファイル名）
                output_path = output_dir / input_path.name

                # CSVとして出力
                critical_df.to_csv(
                    output_path, index=False, encoding="utf-8", na_rep=""
                )

                output_files.append(output_path)
                critical_rows += len(critical_df)

                if verbose:
                    print(
                        f"  ✓ {input_path.name}: {len(critical_df)}行の{severity_filter}を抽出"
                    )

        # 結果サマリー
        if verbose:
            if output_files:
                print(f"\n✅ {severity_filter}抽出完了:")
                print(f"   入力: {len(input_files)}ファイル ({total_rows}行)")
                print(f"   出力: {len(output_files)}ファイル ({critical_rows}行)")
            else:
                print(f"\n⚠️  {severity_filter}行が見つかりませんでした")

        return output_files

    except pd.errors.EmptyDataError:
        raise FilterCriticalError(f"空のCSVファイルです: {input_path}")

    except pd.errors.ParserError as e:
        raise FilterCriticalError(
            f"CSVの解析に失敗しました: {input_path}, エラー: {str(e)}"
        )

    except Exception as e:
        if isinstance(e, FilterCriticalError):
            raise
        raise FilterCriticalError(f"CRITICAL抽出処理中にエラーが発生しました: {str(e)}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "severity_extracted"
    output_dir = project_root / "critical_only"

    print("=" * 60)
    print("Juniper Syslog Filter - CRITICAL抽出 (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"🔍 フィルタ条件: Severity=CRITICAL")
    print()

    try:
        result_files = filter_critical(input_files, output_dir, verbose=True)

        if result_files:
            print(f"\n✅ 処理完了: {len(result_files)}個のファイルを出力しました")
        else:
            print("\n⚠️  CRITICAL行が見つかりませんでした")

    except FilterCriticalError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
