"""
extract_routing.py - routing抽出モジュール（pandas版）

責務:
- reduced_logs/*.csv のMessage列から routing 情報を抽出
- パターン: srcIP/port > dstIP/port → srcIP > dstIP
- 新しい列 routing を追加
- routed_logs/*.csv に出力
- 内部的にpandasで高速処理
"""

from pathlib import Path
from typing import List, Union
import pandas as pd
import re


class ExtractRoutingError(Exception):
    """routing抽出処理のカスタム例外"""

    pass


def extract_routing(
    input_files: List[Path],
    output_dir: Union[str, Path],
    pattern: str = r"(\d+\.\d+\.\d+\.\d+)/\d+\s*>\s*(\d+\.\d+\.\d+\.\d+)/\d+",
    verbose: bool = True,
) -> List[Path]:
    """
    Message列からrouting情報を抽出し、新しい列として追加

    パターン: srcIP/port > dstIP/port → srcIP > dstIP
    例: 192.168.1.5/12345 > 203.0.113.10/80 → 192.168.1.5 > 203.0.113.10

    内部的にpandasで処理し、高速化を実現。
    出力はCSVファイルとして保存され、パスのリストを返す。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        pattern: routing抽出用の正規表現パターン
        verbose: 詳細ログを出力するか

    Returns:
        List[Path]: 出力されたrouting抽出済みCSVファイルのPathリスト

    Raises:
        ExtractRoutingError: routing抽出処理に失敗した場合

    Examples:
        >>> files = extract_routing(csv_files, "routed_logs")
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
            df = pd.read_csv(input_path, encoding="utf-8")

            # Message列の存在確認
            if "Message" not in df.columns:
                raise ExtractRoutingError(
                    f"Message列が見つかりません: {input_path.name}"
                )

            # 正規表現でrouting情報を抽出
            # str.extract() で srcIP と dstIP を抽出
            extracted = df["Message"].str.extract(pattern, expand=True)

            # srcIP > dstIP の形式に結合
            # NaNの場合は空文字列にする
            df["routing"] = extracted[0].fillna("") + " > " + extracted[1].fillna("")

            # 両方が空の場合は空文字列に統一
            df["routing"] = df["routing"].replace(" > ", "", regex=False)

            # 最後にNaNを空文字列に変換（CSVで保存されるときにNaNにならないように）
            df["routing"] = df["routing"].fillna("")

            # 列の順序を調整: Timestamp, Hostname, AppName, routing, Message
            cols = df.columns.tolist()
            # routingをMessageの前に配置
            cols.remove("routing")
            message_idx = cols.index("Message")
            cols.insert(message_idx, "routing")
            df = df[cols]

            # 出力ファイル名を生成（入力と同じファイル名）
            output_path = output_dir / input_path.name

            # pandasでCSVとして出力（NaNを空文字列として保存）
            df.to_csv(output_path, index=False, encoding="utf-8", na_rep="")

            output_files.append(output_path)

            if verbose:
                # routing抽出された行数をカウント
                extracted_count = (df["routing"] != "").sum()
                print(
                    f"  ✓ {input_path.name}: {extracted_count}/{len(df)}行でrouting抽出"
                )

        if verbose and output_files:
            print(f"\n✅ routing抽出完了: {len(output_files)}ファイル処理")

        return output_files

    except pd.errors.EmptyDataError:
        raise ExtractRoutingError(f"空のCSVファイルです: {input_path}")

    except pd.errors.ParserError as e:
        raise ExtractRoutingError(
            f"CSVの解析に失敗しました: {input_path}, エラー: {str(e)}"
        )

    except Exception as e:
        if isinstance(e, ExtractRoutingError):
            raise
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
    print("Juniper Syslog Filter - routing抽出 (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"🔍 抽出パターン: srcIP/port > dstIP/port → srcIP > dstIP")
    print()

    try:
        routed_files = extract_routing(input_files, output_dir, verbose=True)

        if routed_files:
            print(f"\n✅ 処理完了: {len(routed_files)}個のファイルを処理しました")
        else:
            print("\n⚠️  処理されたファイルがありません")

    except ExtractRoutingError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
