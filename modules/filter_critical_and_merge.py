"""
filter_critical_and_merge.py - CRITICAL抽出 + マージモジュール（pandas版）

責務:
- severity_extracted/*.csv から Severity=CRITICAL の行のみを抽出
- 全ファイルを1つにマージ
- critical_merged.csv に出力
- 内部的にpandasで高速処理

処理フロー:
    1. 各CSVファイルから Severity=CRITICAL の行をフィルタ
    2. 全てのDataFrameをpd.concat()でマージ
    3. 単一のCSVファイルとして出力

列構造:
    入力/出力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, protocol, SeverityLevel, Severity, Message]
"""

from pathlib import Path
from typing import List, Union
import pandas as pd


class FilterCriticalError(Exception):
    """CRITICAL抽出処理のカスタム例外"""

    pass


def filter_and_merge_critical(
    input_files: List[Path], output_file: Union[str, Path], verbose: bool = True
) -> Path:
    """
    Severity=CRITICALの行のみを抽出し、全ファイルをマージ

    複数のCSVファイルからSeverity列が'CRITICAL'の行のみを抽出し、
    全てのデータを1つのCSVファイルにマージする。

    内部的にpandasで処理し、高速化を実現。

    Args:
        input_files: 入力CSVファイルのリスト
        output_file: 出力CSVファイルのパス
        verbose: 詳細ログを出力するか

    Returns:
        Path: 出力されたマージ済みCSVファイルのPath

    Raises:
        FilterCriticalError: CRITICAL抽出処理に失敗した場合

    Examples:
        >>> output = filter_and_merge_critical(csv_files, "critical_merged.csv")
    """
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not input_files:
        if verbose:
            print("⚠️  入力ファイルがありません")
        return None

    try:
        critical_dataframes = []
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

            # Severity=CRITICALの行のみフィルタ
            critical_df = df[df["Severity"] == "CRITICAL"]

            if len(critical_df) > 0:
                critical_dataframes.append(critical_df)
                critical_rows += len(critical_df)

                if verbose:
                    print(
                        f"  ✓ {input_path.name}: {len(critical_df)}行のCRITICALを抽出"
                    )

        # CRITICAL行が1つもない場合
        if not critical_dataframes:
            if verbose:
                print("\n⚠️  CRITICAL行が見つかりませんでした")
            return None

        # 全DataFrameをマージ
        merged_df = pd.concat(critical_dataframes, ignore_index=True)

        # CSVとして出力
        merged_df.to_csv(output_file, index=False, encoding="utf-8", na_rep="")

        if verbose:
            print(f"\n✅ CRITICAL抽出 + マージ完了:")
            print(f"   入力: {len(input_files)}ファイル ({total_rows}行)")
            print(f"   出力: {output_file.name} ({critical_rows}行)")

        return output_file

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
    output_file = project_root / "critical_merged.csv"

    print("=" * 60)
    print("Juniper Syslog Filter - CRITICAL抽出 + マージ (pandas版)")
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
        result = filter_and_merge_critical(input_files, output_file, verbose=True)

        if result:
            print(f"\n✅ 処理完了: {result}")
        else:
            print("\n⚠️  CRITICAL行が見つかりませんでした")

    except FilterCriticalError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
