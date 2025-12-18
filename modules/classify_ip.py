"""
classify_ip.py - IP分類モジュール（pandas版）

責務:
- splitted_logs/*.csv の srcIP, dstIP を分類
- IPアドレスが private か global か判定
- srcIP_type, dstIP_type列を追加
- classified_logs/*.csv に出力
- 内部的にpandasで高速処理

プライベートIP範囲:
    10.0.0.0/8     (10.0.0.0 - 10.255.255.255)
    172.16.0.0/12  (172.16.0.0 - 172.31.255.255)
    192.168.0.0/16 (192.168.0.0 - 192.168.255.255)

列構造:
    入力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message]
    出力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, Message]
"""

from pathlib import Path
from typing import List, Union
import pandas as pd


class ClassifyIPError(Exception):
    """IP分類処理のカスタム例外"""

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


def classify_ip(
    input_files: List[Path], output_dir: Union[str, Path], verbose: bool = True
) -> List[Path]:
    """
    srcIP, dstIP を private/global に分類

    各IPアドレスを分類し、srcIP_type, dstIP_type 列を追加。
    srcIP_type は srcIP の直後、dstIP_type は dstIP の直後に挿入。

    内部的にpandasで処理し、高速化を実現。
    出力はCSVファイルとして保存され、パスのリストを返す。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        verbose: 詳細ログを出力するか

    Returns:
        List[Path]: 出力されたIP分類済みCSVファイルのPathリスト

    Raises:
        ClassifyIPError: IP分類処理に失敗した場合

    Examples:
        >>> files = classify_ip(csv_files, "classified_logs")
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

            # srcIP, dstIP列の存在確認
            if "srcIP" not in df.columns:
                raise ClassifyIPError(f"srcIP列が見つかりません: {input_path.name}")
            if "dstIP" not in df.columns:
                raise ClassifyIPError(f"dstIP列が見つかりません: {input_path.name}")

            # IPアドレスを分類（ベクトル演算）
            df["srcIP_type"] = df["srcIP"].apply(classify_ip_address)
            df["dstIP_type"] = df["dstIP"].apply(classify_ip_address)

            # 列の順序を調整
            # 入力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message]
            # 出力: [Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, Message]
            cols = df.columns.tolist()

            # srcIP_type, dstIP_type を削除
            cols.remove("srcIP_type")
            cols.remove("dstIP_type")

            # srcIP の直後に srcIP_type を挿入
            srcip_idx = cols.index("srcIP")
            cols.insert(srcip_idx + 1, "srcIP_type")

            # dstIP の直後に dstIP_type を挿入（srcIP_type が挿入されたので +1）
            dstip_idx = cols.index("dstIP")
            cols.insert(dstip_idx + 1, "dstIP_type")

            df = df[cols]

            # 出力ファイル名を生成（入力と同じファイル名）
            output_path = output_dir / input_path.name

            # pandasでCSVとして出力（NaNを空文字列として保存）
            df.to_csv(output_path, index=False, encoding="utf-8", na_rep="")

            output_files.append(output_path)

            if verbose:
                # private IP数をカウント
                private_src_count = (df["srcIP_type"] == "private").sum()
                private_dst_count = (df["dstIP_type"] == "private").sum()
                print(
                    f"  ✓ {input_path.name}: {len(df)}行処理 (private srcIP: {private_src_count}, private dstIP: {private_dst_count})"
                )

        if verbose and output_files:
            print(f"\n✅ IP分類完了: {len(output_files)}ファイル処理")

        return output_files

    except pd.errors.EmptyDataError:
        raise ClassifyIPError(f"空のCSVファイルです: {input_path}")

    except pd.errors.ParserError as e:
        raise ClassifyIPError(
            f"CSVの解析に失敗しました: {input_path}, エラー: {str(e)}"
        )

    except Exception as e:
        if isinstance(e, ClassifyIPError):
            raise
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
    print("Juniper Syslog Filter - IP分類 (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"🔍 分類: private (10.x, 172.16-31.x, 192.168.x) / global")
    print()

    try:
        classified_files = classify_ip(input_files, output_dir, verbose=True)

        if classified_files:
            print(f"\n✅ 処理完了: {len(classified_files)}個のファイルを処理しました")
        else:
            print("\n⚠️  処理されたファイルがありません")

    except ClassifyIPError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
