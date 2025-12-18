"""
extract_severity.py - Severity抽出モジュール（pandas版）

責務:
- severity_level_extracted/*.csv のMessage列から Severity 情報を抽出
- パターン: Severity=xxx → Severity列に抽出
- Severity列をMessage列の直前に追加
- severity_extracted/*.csv に出力
- 内部的にpandasで高速処理

列構造:
    入力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, protocol, SeverityLevel, Message]
    出力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, protocol, SeverityLevel, Severity, Message]
"""

from pathlib import Path
from typing import List, Union
import pandas as pd
import re


class ExtractSeverityError(Exception):
    """Severity抽出処理のカスタム例外"""

    pass


def extract_severity(
    input_files: List[Path], output_dir: Union[str, Path], verbose: bool = True
) -> List[Path]:
    """
    Message列からSeverity情報を抽出し、新しい列として追加

    パターン: Severity=xxx → Severity列
    例: Severity=WARNING → "WARNING"

    内部的にpandasで処理し、高速化を実現。
    出力はCSVファイルとして保存され、パスのリストを返す。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        verbose: 詳細ログを出力するか

    Returns:
        List[Path]: 出力されたSeverity抽出済みCSVファイルのPathリスト

    Raises:
        ExtractSeverityError: Severity抽出処理に失敗した場合

    Examples:
        >>> files = extract_severity(csv_files, "severity_extracted")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_files:
        if verbose:
            print("⚠️  入力ファイルがありません")
        return []

    output_files = []

    # 正規表現パターン: Severity=xxx
    pattern = r"Severity=(\w+)"

    try:
        for input_path in input_files:
            # pandasでCSVを読み込み
            df = pd.read_csv(input_path, encoding="utf-8", keep_default_na=False)

            # Message列の存在確認
            if "Message" not in df.columns:
                raise ExtractSeverityError(
                    f"Message列が見つかりません: {input_path.name}"
                )

            # 正規表現でSeverity情報を抽出
            # str.extract() で Severity値を抽出
            extracted = df["Message"].str.extract(pattern, expand=False)

            # Severity列として追加（マッチしない場合は空文字列）
            df["Severity"] = extracted.fillna("")

            # 列の順序を調整: Severity を Message の直前に配置
            cols = df.columns.tolist()
            cols.remove("Severity")
            message_idx = cols.index("Message")
            cols.insert(message_idx, "Severity")
            df = df[cols]

            # 出力ファイル名を生成（入力と同じファイル名）
            output_path = output_dir / input_path.name

            # pandasでCSVとして出力（NaNを空文字列として保存）
            df.to_csv(output_path, index=False, encoding="utf-8", na_rep="")

            output_files.append(output_path)

            if verbose:
                # Severity抽出された行数をカウント
                extracted_count = (df["Severity"] != "").sum()
                print(
                    f"  ✓ {input_path.name}: {extracted_count}/{len(df)}行でSeverity抽出"
                )

        if verbose and output_files:
            print(f"\n✅ Severity抽出完了: {len(output_files)}ファイル処理")

        return output_files

    except pd.errors.EmptyDataError:
        raise ExtractSeverityError(f"空のCSVファイルです: {input_path}")

    except pd.errors.ParserError as e:
        raise ExtractSeverityError(
            f"CSVの解析に失敗しました: {input_path}, エラー: {str(e)}"
        )

    except Exception as e:
        if isinstance(e, ExtractSeverityError):
            raise
        raise ExtractSeverityError(
            f"Severity抽出処理中にエラーが発生しました: {str(e)}"
        )


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "severity_level_extracted"
    output_dir = project_root / "severity_extracted"

    print("=" * 60)
    print("Juniper Syslog Filter - Severity抽出 (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"🔍 抽出パターン: Severity=xxx")
    print()

    try:
        severity_files = extract_severity(input_files, output_dir, verbose=True)

        if severity_files:
            print(f"\n✅ 処理完了: {len(severity_files)}個のファイルを処理しました")
        else:
            print("\n⚠️  処理されたファイルがありません")

    except ExtractSeverityError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
