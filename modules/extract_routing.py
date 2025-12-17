"""
extract_routing.py - routing列抽出モジュール

責務:
- reduced_logs/*.csv のMessage列から routing情報を抽出
- srcIP/port > dstIP/port から srcIP > dstIP を抽出
- routing列としてMessage列の前に追加
- routed_logs/*.csv に出力

列構造:
    入力: [Timestamp, Hostname, AppName, Message]
    出力: [Timestamp, Hostname, AppName, routing, Message]
"""

import csv
import re
from pathlib import Path
from typing import List, Optional


class ExtractRoutingError(Exception):
    """routing抽出時のカスタム例外"""

    pass


# 正規表現パターン: srcIP/port > dstIP/port
ROUTING_PATTERN = re.compile(
    r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+ > (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+"
)


def extract_routing_from_message(message: str) -> Optional[str]:
    """
    Message列からrouting情報を抽出

    Args:
        message: Message列の文字列

    Returns:
        "srcIP > dstIP" 形式の文字列、抽出できない場合はNone

    Example:
        >>> extract_routing_from_message("Attack 10.0.0.5/12345 > 203.0.113.10/80 protocol=tcp")
        "10.0.0.5 > 203.0.113.10"
    """
    match = ROUTING_PATTERN.search(message)

    if match:
        src_ip = match.group(1)
        dst_ip = match.group(2)
        return f"{src_ip} > {dst_ip}"

    return None


def extract_routing_from_csv(
    input_path: Path, output_path: Path, verbose: bool = False
) -> int:
    """
    単一CSVファイルからrouting列を抽出して追加

    Args:
        input_path: 入力CSVファイル
        output_path: 出力CSVファイル
        verbose: 詳細ログを出力するか

    Returns:
        処理した行数

    Raises:
        FileNotFoundError: 入力ファイルが存在しない場合
        ExtractRoutingError: 処理中にエラーが発生した場合
    """
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    try:
        row_count = 0
        routing_found_count = 0

        with open(input_path, "r", encoding="utf-8", newline="") as infile, open(
            output_path, "w", encoding="utf-8", newline=""
        ) as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # ヘッダー行処理
            header = next(reader, None)
            if header:
                # routing列を Message列の前に挿入
                # 入力: [Timestamp, Hostname, AppName, Message]
                # 出力: [Timestamp, Hostname, AppName, routing, Message]
                new_header = header[:3] + ["routing"] + [header[3]]
                writer.writerow(new_header)
                row_count += 1

            # データ行処理
            for row in reader:
                if len(row) >= 4:
                    # Message列（インデックス3）からrouting抽出
                    message = row[3]
                    routing = extract_routing_from_message(message)

                    if routing:
                        routing_found_count += 1
                    else:
                        routing = ""  # 抽出できない場合は空文字

                    # routing列を挿入
                    new_row = row[:3] + [routing] + [row[3]]
                    writer.writerow(new_row)
                    row_count += 1

        if verbose:
            print(f"  ✓ {row_count}行処理 (routing抽出: {routing_found_count}行)")

        return row_count

    except Exception as e:
        raise ExtractRoutingError(f"routing抽出中にエラーが発生しました: {str(e)}")


def extract_routing(
    input_files: List[Path], output_dir: Path, verbose: bool = False
) -> List[Path]:
    """
    複数のCSVファイルからrouting列を抽出して追加

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力ディレクトリ
        verbose: 詳細ログを出力するか

    Returns:
        出力されたファイルのリスト

    Raises:
        ExtractRoutingError: 処理に失敗した場合
    """
    if not input_files:
        if verbose:
            print("⚠️  処理するファイルがありません")
        return []

    # 出力ディレクトリが存在しない場合は作成
    output_dir.mkdir(parents=True, exist_ok=True)

    output_files = []

    try:
        for input_file in sorted(input_files):
            if verbose:
                print(f"📄 処理中: {input_file.name}")

            # 出力ファイル名は入力と同じ
            output_path = output_dir / input_file.name

            # routing抽出処理
            extract_routing_from_csv(input_file, output_path, verbose=verbose)

            output_files.append(output_path)

        if verbose:
            print(f"\n✅ 処理完了: {len(output_files)}個のファイルを作成")

        return output_files

    except Exception as e:
        raise ExtractRoutingError(f"routing抽出処理中にエラーが発生しました: {str(e)}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "reduced_logs"
    output_dir = project_root / "routed_logs"

    print("=" * 60)
    print("Juniper Syslog Filter - routing抽出モジュール")
    print("=" * 60)

    try:
        # 入力CSVファイルを取得
        csv_files = sorted(input_dir.glob("*.csv"))

        if not csv_files:
            print(f"\n⚠️  CSVファイルが見つかりませんでした: {input_dir}")
            return 0

        print(f"\n対象ファイル数: {len(csv_files)}")
        print(f"抽出パターン: srcIP/port > dstIP/port → srcIP > dstIP")
        print()

        output_files = extract_routing(csv_files, output_dir, verbose=True)

        if output_files:
            print(f"\n✅ 処理完了: {len(output_files)}個のファイルを作成しました")
        else:
            print("\n⚠️  処理するデータがありませんでした")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
