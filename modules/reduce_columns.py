"""
reduce_columns.py - 列削減モジュール（pandas版）

責務:
- merged_logs/*.csv から不要列を削除
- 指定された列のみを保持
- reduced_logs/*.csv に出力
- 内部的にpandasで高速処理
"""

from pathlib import Path
from typing import List, Union
import pandas as pd


class ReduceColumnsError(Exception):
    """列削減処理のカスタム例外"""

    pass


def reduce_columns(
    input_files: List[Path],
    output_dir: Union[str, Path],
    keep_columns: List[int] = [0, 1, 2, 6],
    verbose: bool = True,
) -> List[Path]:
    """
    CSVファイルから指定された列のみを保持

    内部的にpandasで処理し、高速化を実現。
    出力はCSVファイルとして保存され、パスのリストを返す。

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        keep_columns: 保持する列のインデックスリスト（デフォルト: [0,1,2,6]）
        verbose: 詳細ログを出力するか

    Returns:
        List[Path]: 出力された列削減済みCSVファイルのPathリスト

    Raises:
        ReduceColumnsError: 列削減処理に失敗した場合

    Examples:
        >>> files = reduce_columns(csv_files, "reduced_logs")
        >>> files = reduce_columns(csv_files, "reduced_logs", keep_columns=[0,1,2])
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

            # 列数の検証
            total_columns = len(df.columns)

            # keep_columnsの範囲チェック
            for col_idx in keep_columns:
                if col_idx >= total_columns or col_idx < 0:
                    raise ReduceColumnsError(
                        f"列インデックス {col_idx} が範囲外です（0-{total_columns-1}）: {input_path.name}"
                    )

            # 指定された列のみを選択
            reduced_df = df.iloc[:, keep_columns]

            # 出力ファイル名を生成（入力と同じファイル名）
            output_path = output_dir / input_path.name

            # pandasでCSVとして出力
            reduced_df.to_csv(output_path, index=False, encoding="utf-8")

            output_files.append(output_path)

            if verbose:
                print(
                    f"  ✓ {input_path.name}: {len(df.columns)}列 → {len(reduced_df.columns)}列"
                )

        if verbose and output_files:
            print(f"\n✅ 列削減完了: {len(output_files)}ファイル処理")

        return output_files

    except pd.errors.EmptyDataError:
        raise ReduceColumnsError(f"空のCSVファイルです: {input_path}")

    except pd.errors.ParserError as e:
        raise ReduceColumnsError(
            f"CSVの解析に失敗しました: {input_path}, エラー: {str(e)}"
        )

    except Exception as e:
        if isinstance(e, ReduceColumnsError):
            raise
        raise ReduceColumnsError(f"列削減処理中にエラーが発生しました: {str(e)}")


def main():
    """
    スタンドアロン実行用のメイン関数
    """
    # デフォルトパス設定
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "merged_logs"
    output_dir = project_root / "reduced_logs"

    print("=" * 60)
    print("Juniper Syslog Filter - 列削減 (pandas版)")
    print("=" * 60)

    # 入力ファイルを取得
    input_files = sorted(input_dir.glob("*.csv"))

    if not input_files:
        print(f"\n⚠️  入力ファイルが見つかりません: {input_dir}")
        return 0

    print(f"📄 対象ファイル数: {len(input_files)}")
    print(f"📋 保持する列: [0, 1, 2, 6] (Timestamp, Hostname, AppName, Message)")
    print()

    try:
        reduced_files = reduce_columns(
            input_files, output_dir, keep_columns=[0, 1, 2, 6], verbose=True
        )

        if reduced_files:
            print(f"\n✅ 処理完了: {len(reduced_files)}個のファイルを処理しました")
        else:
            print("\n⚠️  処理されたファイルがありません")

    except ReduceColumnsError as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
