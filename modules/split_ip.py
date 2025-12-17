"""
split_ip.py - IP分割モジュール

責務:
- routed_logs/*.csv のrouting列を分割
- routing列から srcIP と dstIP を抽出
- srcIP, dstIP列をrouting列の後ろに追加
- splitted_logs/*.csv に出力

列構造:
    入力: [Timestamp, Hostname, AppName, routing, Message]
    出力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message]
"""

import csv
from pathlib import Path
from typing import List, Tuple, Optional


class SplitIPError(Exception):
    """IP分割時のカスタム例外"""

    pass


def split_routing(routing: str) -> Tuple[str, str]:
    """
    routing列を srcIP と dstIP に分割

    Args:
        routing: "srcIP > dstIP" 形式の文字列

    Returns:
        (srcIP, dstIP) のタプル、分割できない場合は ("", "")

    Example:
        >>> split_routing("192.168.1.1 > 10.0.0.5")
        ("192.168.1.1", "10.0.0.5")
    """
    if not routing or routing.strip() == "":
        return ("", "")

    # " > " で分割
    parts = routing.split(" > ")

    if len(parts) == 2:
        return (parts[0].strip(), parts[1].strip())
    else:
        return ("", "")


def split_ip_from_csv(
    input_path: Path, output_path: Path, verbose: bool = False
) -> int:
    """
    単一CSVファイルからrouting列を分割してsrcIP, dstIP列を追加

    Args:
        input_path: 入力CSVファイル
        output_path: 出力CSVファイル
        verbose: 詳細ログを出力するか

    Returns:
        処理した行数

    Raises:
        FileNotFoundError: 入力ファイルが存在しない場合
        SplitIPError: 処理中にエラーが発生した場合
    """
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    try:
        row_count = 0
        split_success_count = 0

        with open(input_path, "r", encoding="utf-8", newline="") as infile, open(
            output_path, "w", encoding="utf-8", newline=""
        ) as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # ヘッダー行処理
            header = next(reader, None)
            if header:
                # srcIP, dstIP列をrouting列の後ろに追加
                # 入力: [Timestamp, Hostname, AppName, routing, Message]
                # 出力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message]
                new_header = header[:4] + ["srcIP", "dstIP"] + [header[4]]
                writer.writerow(new_header)
                row_count += 1

            # データ行処理
            for row in reader:
                if len(row) >= 5:
                    # routing列（インデックス3）を分割
                    routing = row[3]
                    src_ip, dst_ip = split_routing(routing)

                    if src_ip and dst_ip:
                        split_success_count += 1

                    # srcIP, dstIP列を挿入
                    new_row = row[:4] + [src_ip, dst_ip] + [row[4]]
                    writer.writerow(new_row)
                    row_count += 1

        if verbose:
            print(f"  ✓ {row_count}行処理 (IP分割成功: {split_success_count}行)")

        return row_count

    except Exception as e:
        raise SplitIPError(f"IP分割中にエラーが発生しました: {str(e)}")


def split_ip(
    input_files: List[Path], output_dir: Path, verbose: bool = False
) -> List[Path]:
    """
    複数のCSVファイルからrouting列を分割してsrcIP, dstIP列を追加

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力ディレクトリ
        verbose: 詳細ログを出力するか

    Returns:
        出力されたファイルのリスト

    Raises:
        SplitIPError: 処理に失敗した場合
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

            # IP分割処理
            split_ip_from_csv(input_file, output_path, verbose=verbose)

            output_files.append(output_path)

        if verbose:
            print(f"\n✅ 処理完了: {len(output_files)}個のファイルを作成")

        return output_files

    except Exception as e:
        raise SplitIPError(f"IP分割処理中にエラーが発生しました: {str(e)}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "routed_logs"
    output_dir = project_root / "splitted_logs"

    print("=" * 60)
    print("Juniper Syslog Filter - IP分割モジュール")
    print("=" * 60)

    try:
        # 入力CSVファイルを取得
        csv_files = sorted(input_dir.glob("*.csv"))

        if not csv_files:
            print(f"\n⚠️  CSVファイルが見つかりませんでした: {input_dir}")
            return 0

        print(f"\n対象ファイル数: {len(csv_files)}")
        print(f"分割パターン: routing → srcIP, dstIP")
        print()

        output_files = split_ip(csv_files, output_dir, verbose=True)

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
