"""
split_ip.py - IP分割モジュール（pandas版）

責務:
- routed_logs/*.csv のrouting列を分割
- routing列から srcIP と dstIP を抽出
- srcIP, dstIP列をrouting列の後ろに追加
- splitted_logs/*.csv に出力
- 内部的にpandasで高速処理

列構造:
    入力: [Timestamp, Hostname, AppName, routing, Message]
    出力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message]
"""

from pathlib import Path
from typing import List, Union
import pandas as pd


class SplitIPError(Exception):
    """IP分割処理のカスタム例外"""

    pass


def split_ip(
    input_files: List[Path],
    output_dir: Union[str, Path],
    delimiter: str = " > ",
    verbose: bool = True,
) -> List[Path]:
    """
    routing列を srcIP と dstIP に分割

    routing列（"srcIP > dstIP"）を分割し、
    新しい列 srcIP, dstIP を routing の後ろに追加。

    内部的にpandasで処理し、高速化を実現。
    出力はCSVファイルとして保存され、パスのリストを返す。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        delimiter: routing列の区切り文字
        verbose: 詳細ログを出力するか

    Returns:
        List[Path]: 出力されたIP分割済みCSVファイルのPathリスト

    Raises:
        SplitIPError: IP分割処理に失敗した場合

    Examples:
        >>> files = split_ip(csv_files, "splitted_logs")
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

            # routing列の存在確認
            if "routing" not in df.columns:
                raise SplitIPError(f"routing列が見つかりません: {input_path.name}")

            # routing列を delimiter で分割（ベクトル演算）
            # expand=True で別々の列に分割
            split_result = df["routing"].str.split(delimiter, expand=True, n=1)

            # 分割結果を srcIP, dstIP 列として追加
            # 分割できない場合（routing列が空）は空文字列
            df["srcIP"] = split_result[0] if 0 in split_result.columns else ""
            df["dstIP"] = split_result[1] if 1 in split_result.columns else ""

            # NaNを空文字列に変換
            df["srcIP"] = df["srcIP"].fillna("")
            df["dstIP"] = df["dstIP"].fillna("")

            # 列の順序を調整: routing の後ろに srcIP, dstIP を配置
            # 入力: [Timestamp, Hostname, AppName, routing, Message]
            # 出力: [Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message]
            cols = df.columns.tolist()

            # srcIP, dstIP を routing の後ろに移動
            cols.remove("srcIP")
            cols.remove("dstIP")
            routing_idx = cols.index("routing")
            cols.insert(routing_idx + 1, "srcIP")
            cols.insert(routing_idx + 2, "dstIP")

            df = df[cols]

            # 出力ファイル名を生成（入力と同じファイル名）
            output_path = output_dir / input_path.name

            # pandasでCSVとして出力（NaNを空文字列として保存）
            df.to_csv(output_path, index=False, encoding="utf-8", na_rep="")

            output_files.append(output_path)

            if verbose:
                # IP分割成功数をカウント
                split_success_count = ((df["srcIP"] != "") & (df["dstIP"] != "")).sum()
                print(
                    f"  ✓ {input_path.name}: {len(df)}行処理 (IP分割成功: {split_success_count}行)"
                )

        if verbose and output_files:
            print(f"\n✅ IP分割完了: {len(output_files)}ファイル処理")

        return output_files

    except pd.errors.EmptyDataError:
        raise SplitIPError(f"空のCSVファイルです: {input_path}")

    except pd.errors.ParserError as e:
        raise SplitIPError(f"CSVの解析に失敗しました: {input_path}, エラー: {str(e)}")

    except Exception as e:
        if isinstance(e, SplitIPError):
            raise
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
    print("Juniper Syslog Filter - IP分割 (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"🔍 分割パターン: routing → srcIP, dstIP")
    print()

    try:
        splitted_files = split_ip(input_files, output_dir, verbose=True)

        if splitted_files:
            print(f"\n✅ 処理完了: {len(splitted_files)}個のファイルを処理しました")
        else:
            print("\n⚠️  処理されたファイルがありません")

    except SplitIPError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
