"""
classify_ip.py - IP分類モジュール

責務:
- splitted_logs/*.csv の srcIP, dstIP を分類
- IPアドレスが private か global か判定
- srcIP_type, dstIP_type列を追加
- classified_logs/*.csv に出力

プライベートIP範囲:
    10.0.0.0/8     (10.0.0.0 - 10.255.255.255)
    172.16.0.0/12  (172.16.0.0 - 172.31.255.255)
    192.168.0.0/16 (192.168.0.0 - 192.168.255.255)

列構造:
    入力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message]
    出力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, srcIP_type, dstIP_type, Message]
"""

import csv
from pathlib import Path
from typing import List


class ClassifyIPError(Exception):
    """IP分類時のカスタム例外"""

    pass


def is_private_ip(ip: str) -> bool:
    """
    IPアドレスがプライベートIPかどうか判定

    Args:
        ip: IPアドレス文字列

    Returns:
        プライベートIPの場合True、それ以外False

    Example:
        >>> is_private_ip("192.168.1.1")
        True
        >>> is_private_ip("8.8.8.8")
        False
    """
    if not ip or ip.strip() == "":
        return False

    try:
        # IPアドレスをオクテットに分割
        parts = ip.split(".")
        if len(parts) != 4:
            return False

        octets = [int(part) for part in parts]

        # 範囲チェック（0-255）
        if not all(0 <= octet <= 255 for octet in octets):
            return False

        # プライベートIP範囲の判定
        # 10.0.0.0/8
        if octets[0] == 10:
            return True

        # 172.16.0.0/12
        if octets[0] == 172 and 16 <= octets[1] <= 31:
            return True

        # 192.168.0.0/16
        if octets[0] == 192 and octets[1] == 168:
            return True

        return False

    except (ValueError, IndexError):
        return False


def classify_ip_address(ip: str) -> str:
    """
    IPアドレスを分類

    Args:
        ip: IPアドレス文字列

    Returns:
        "private" または "global"、空の場合は ""

    Example:
        >>> classify_ip_address("192.168.1.1")
        "private"
        >>> classify_ip_address("8.8.8.8")
        "global"
    """
    if not ip or ip.strip() == "":
        return ""

    return "private" if is_private_ip(ip) else "global"


def classify_ip_from_csv(
    input_path: Path, output_path: Path, verbose: bool = False
) -> int:
    """
    単一CSVファイルからIPアドレスを分類してsrcIP_type, dstIP_type列を追加

    Args:
        input_path: 入力CSVファイル
        output_path: 出力CSVファイル
        verbose: 詳細ログを出力するか

    Returns:
        処理した行数

    Raises:
        FileNotFoundError: 入力ファイルが存在しない場合
        ClassifyIPError: 処理中にエラーが発生した場合
    """
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    try:
        row_count = 0
        private_src_count = 0
        private_dst_count = 0

        with open(input_path, "r", encoding="utf-8", newline="") as infile, open(
            output_path, "w", encoding="utf-8", newline=""
        ) as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # ヘッダー行処理
            header = next(reader, None)
            if header:
                # srcIP_type, dstIP_type列をdstIP列の後ろに追加
                # 入力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message]
                # 出力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, Message]
                new_header = (
                    header[:5]
                    + ["srcIP_type"]
                    + [header[5]]
                    + ["dstIP_type"]
                    + [header[6]]
                )
                writer.writerow(new_header)
                row_count += 1

            # データ行処理
            for row in reader:
                if len(row) >= 7:
                    # srcIP（インデックス4）とdstIP（インデックス5）を分類
                    src_ip = row[4]
                    dst_ip = row[5]

                    src_ip_type = classify_ip_address(src_ip)
                    dst_ip_type = classify_ip_address(dst_ip)

                    if src_ip_type == "private":
                        private_src_count += 1
                    if dst_ip_type == "private":
                        private_dst_count += 1

                    # srcIP_type, dstIP_type列を挿入
                    new_row = (
                        row[:5] + [src_ip_type] + [row[5]] + [dst_ip_type] + [row[6]]
                    )
                    writer.writerow(new_row)
                    row_count += 1

        if verbose:
            print(
                f"  ✓ {row_count}行処理 (private srcIP: {private_src_count}, private dstIP: {private_dst_count})"
            )

        return row_count

    except Exception as e:
        raise ClassifyIPError(f"IP分類中にエラーが発生しました: {str(e)}")


def classify_ip(
    input_files: List[Path], output_dir: Path, verbose: bool = False
) -> List[Path]:
    """
    複数のCSVファイルからIPアドレスを分類してsrcIP_type, dstIP_type列を追加

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力ディレクトリ
        verbose: 詳細ログを出力するか

    Returns:
        出力されたファイルのリスト

    Raises:
        ClassifyIPError: 処理に失敗した場合
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

            # IP分類処理
            classify_ip_from_csv(input_file, output_path, verbose=verbose)

            output_files.append(output_path)

        if verbose:
            print(f"\n✅ 処理完了: {len(output_files)}個のファイルを作成")

        return output_files

    except Exception as e:
        raise ClassifyIPError(f"IP分類処理中にエラーが発生しました: {str(e)}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "splitted_logs"
    output_dir = project_root / "classified_logs"

    print("=" * 60)
    print("Juniper Syslog Filter - IP分類モジュール")
    print("=" * 60)

    try:
        # 入力CSVファイルを取得
        csv_files = sorted(input_dir.glob("*.csv"))

        if not csv_files:
            print(f"\n⚠️  CSVファイルが見つかりませんでした: {input_dir}")
            return 0

        print(f"\n対象ファイル数: {len(csv_files)}")
        print(f"分類: private (10.x, 172.16-31.x, 192.168.x) / global")
        print()

        output_files = classify_ip(csv_files, output_dir, verbose=True)

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
