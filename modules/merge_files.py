"""
merge_files.py - CSVマージモジュール（pandas版）

責務:
- filtered_logs/*.csv を結合
- 80万行単位で分割してマージ
- merged_logs/*.csv に出力
- 内部的にpandasで高速処理
"""

from pathlib import Path
from typing import List, Union
import pandas as pd


class MergeError(Exception):
    """マージ処理のカスタム例外"""

    pass


def merge_csv_files(
    input_files: List[Path],
    output_dir: Union[str, Path],
    max_rows: int = 800000,
    verbose: bool = True,
) -> List[Path]:
    """
    複数のCSVファイルをマージし、指定行数で分割

    内部的にpandasで処理し、高速化を実現。
    出力はCSVファイルとして保存され、パスのリストを返す。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        max_rows: 1ファイルあたりの最大行数（デフォルト: 800000）
        verbose: 詳細ログを出力するか

    Returns:
        List[Path]: 出力されたマージ済みCSVファイルのPathリスト

    Raises:
        MergeError: マージ処理に失敗した場合

    Examples:
        >>> files = merge_csv_files(csv_files, "merged_logs")
        >>> files = merge_csv_files(csv_files, "merged_logs", max_rows=500000)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_files:
        if verbose:
            print("⚠️  入力ファイルがありません")
        return []

    try:
        # 全てのCSVをpandasで読み込み、リストに格納
        df_list = []

        for input_path in input_files:
            try:
                df = pd.read_csv(input_path, encoding="utf-8")

                # 空のDataFrameはスキップ
                if len(df) > 0:
                    df_list.append(df)

            except pd.errors.EmptyDataError:
                # 空のCSVファイルはスキップ
                if verbose:
                    print(f"⚠️  空のファイルをスキップ: {input_path.name}")
                continue
            except Exception as e:
                raise MergeError(
                    f"ファイルの読み込みに失敗: {input_path}, エラー: {str(e)}"
                )

        if not df_list:
            if verbose:
                print("⚠️  有効なデータが見つかりませんでした")
            return []

        # 全DataFrameを結合
        merged_df = pd.concat(df_list, ignore_index=True)
        total_rows = len(merged_df)

        if verbose:
            print(f"📊 総行数: {total_rows:,}行")

        # max_rows単位で分割して出力
        output_files = []
        file_count = 0

        for start_idx in range(0, total_rows, max_rows):
            end_idx = min(start_idx + max_rows, total_rows)
            chunk_df = merged_df.iloc[start_idx:end_idx]

            # 出力ファイル名を生成（merged_000.csv, merged_001.csv, ...）
            output_path = output_dir / f"merged_{file_count:03d}.csv"

            # pandasでCSVとして出力
            chunk_df.to_csv(output_path, index=False, encoding="utf-8")

            output_files.append(output_path)

            if verbose:
                print(f"  ✓ {output_path.name}: {len(chunk_df):,}行")

            file_count += 1

        if verbose:
            print(f"\n✅ マージ完了: {len(output_files)}ファイル作成")

        return output_files

    except pd.errors.ParserError as e:
        raise MergeError(f"CSVの解析に失敗しました: {str(e)}")

    except Exception as e:
        raise MergeError(f"マージ処理中にエラーが発生しました: {str(e)}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "filtered_logs"
    output_dir = project_root / "merged_logs"

    print("=" * 60)
    print("Juniper Syslog Filter - CSVマージ (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"📦 最大行数/ファイル: 800,000行")
    print()

    try:
        merged_files = merge_csv_files(
            input_files, output_dir, max_rows=800000, verbose=True
        )

        if merged_files:
            print(f"\n✅ 処理完了: {len(merged_files)}個のマージファイルを作成しました")
        else:
            print("\n⚠️  マージされたファイルがありません")

    except MergeError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
