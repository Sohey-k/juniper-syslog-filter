"""
extract_protocol.py - protocol抽出モジュール（pandas版）

責務:
- classified_logs/*.csv のMessage列から protocol 情報を抽出
- パターン: protocol=xxx → protocol列に抽出
- protocol列をMessage列の直前に追加
- protocol_extracted/*.csv に出力
- 内部的にpandasで高速処理

列構造:
    入力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, Message]
    出力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, protocol, Message]
"""

from pathlib import Path
from typing import List, Union
import pandas as pd
import re


class ExtractProtocolError(Exception):
    """protocol抽出処理のカスタム例外"""

    pass


def extract_protocol(
    input_files: List[Path],
    output_dir: Union[str, Path],
    pattern: str = r"protocol=(\w+)",
    verbose: bool = True,
) -> List[Path]:
    """
    Message列からprotocol情報を抽出し、新しい列として追加

    パターン: protocol=xxx → protocol列
    例: protocol=tcp → "tcp"

    内部的にpandasで処理し、高速化を実現。
    出力はCSVファイルとして保存され、パスのリストを返す。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        pattern: protocol抽出用の正規表現パターン
        verbose: 詳細ログを出力するか

    Returns:
        List[Path]: 出力されたprotocol抽出済みCSVファイルのPathリスト

    Raises:
        ExtractProtocolError: protocol抽出処理に失敗した場合

    Examples:
        >>> files = extract_protocol(csv_files, "protocol_extracted")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_files:
        if verbose:
            print("⚠️  入力ファイルがありません")
        return []

    output_files = []

    try:
        for input_path in input_files:
            # pandasでCSVを読み込み
            df = pd.read_csv(input_path, encoding="utf-8", keep_default_na=False)

            # Message列の存在確認
            if "Message" not in df.columns:
                raise ExtractProtocolError(
                    f"Message列が見つかりません: {input_path.name}"
                )

            # 正規表現でprotocol情報を抽出
            # str.extract() で protocol値を抽出
            extracted = df["Message"].str.extract(pattern, expand=False)

            # protocol列として追加（マッチしない場合は空文字列）
            df["protocol"] = extracted.fillna("")

            # 列の順序を調整: protocol を Message の直前に配置
            cols = df.columns.tolist()
            cols.remove("protocol")
            message_idx = cols.index("Message")
            cols.insert(message_idx, "protocol")
            df = df[cols]

            # 出力ファイル名を生成（入力と同じファイル名）
            output_path = output_dir / input_path.name

            # pandasでCSVとして出力（NaNを空文字列として保存）
            df.to_csv(output_path, index=False, encoding="utf-8", na_rep="")

            output_files.append(output_path)

            if verbose:
                # protocol抽出された行数をカウント
                extracted_count = (df["protocol"] != "").sum()
                print(
                    f"  ✓ {input_path.name}: {extracted_count}/{len(df)}行でprotocol抽出"
                )

        if verbose and output_files:
            print(f"\n✅ protocol抽出完了: {len(output_files)}ファイル処理")

        return output_files

    except pd.errors.EmptyDataError:
        raise ExtractProtocolError(f"空のCSVファイルです: {input_path}")

    except pd.errors.ParserError as e:
        raise ExtractProtocolError(
            f"CSVの解析に失敗しました: {input_path}, エラー: {str(e)}"
        )

    except Exception as e:
        if isinstance(e, ExtractProtocolError):
            raise
        raise ExtractProtocolError(
            f"protocol抽出処理中にエラーが発生しました: {str(e)}"
        )


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "classified_logs"
    output_dir = project_root / "protocol_extracted"

    print("=" * 60)
    print("Juniper Syslog Filter - protocol抽出 (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"🔍 抽出パターン: protocol=xxx")
    print()

    try:
        protocol_files = extract_protocol(input_files, output_dir, verbose=True)

        if protocol_files:
            print(f"\n✅ 処理完了: {len(protocol_files)}個のファイルを処理しました")
        else:
            print("\n⚠️  処理されたファイルがありません")

    except ExtractProtocolError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
