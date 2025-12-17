"""
reduce_columns.py - 列削減モジュール

責務:
- merged_logs/*.csv から不要な列を削除
- 指定された列インデックスのみ保持
- reduced_logs/*.csv に出力

列インデックス:
    0: Timestamp
    1: Hostname
    2: AppName
    3: SeverityLevel
    4: Severity
    5: LogType
    6: Message
"""

import csv
from pathlib import Path
from typing import List


class ReduceColumnsError(Exception):
    """列削減時のカスタム例外"""

    pass


def reduce_csv_columns(
    input_path: Path, output_path: Path, keep_columns: List[int]
) -> int:
    """
    単一CSVファイルから指定列のみ抽出

    Args:
        input_path: 入力CSVファイル
        output_path: 出力CSVファイル
        keep_columns: 保持する列のインデックスリスト（0始まり）

    Returns:
        処理した行数

    Raises:
        FileNotFoundError: 入力ファイルが存在しない場合
        ReduceColumnsError: 処理中にエラーが発生した場合
    """
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    try:
        row_count = 0

        with open(input_path, "r", encoding="utf-8", newline="") as infile, open(
            output_path, "w", encoding="utf-8", newline=""
        ) as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            for row in reader:
                # 指定された列のみ抽出
                reduced_row = [row[i] for i in keep_columns if i < len(row)]
                writer.writerow(reduced_row)
                row_count += 1

        return row_count

    except Exception as e:
        raise ReduceColumnsError(f"列削減中にエラーが発生しました: {str(e)}")


def reduce_columns(
    input_files: List[Path],
    output_dir: Path,
    keep_columns: List[int] = [
        0,
        1,
        2,
        6,
    ],  # デフォルト: Timestamp, Hostname, AppName, Message
    verbose: bool = False,
) -> List[Path]:
    """
    複数のCSVファイルから指定列のみ抽出

    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力ディレクトリ
        keep_columns: 保持する列のインデックスリスト（デフォルト: [0, 1, 2, 6]）
        verbose: 詳細ログを出力するか

    Returns:
        出力されたファイルのリスト

    Raises:
        ReduceColumnsError: 処理に失敗した場合
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

            # 列削減処理
            row_count = reduce_csv_columns(input_file, output_path, keep_columns)

            output_files.append(output_path)

            if verbose:
                print(f"  ✓ {row_count}行処理 → {output_path.name}")

        if verbose:
            print(f"\n✅ 処理完了: {len(output_files)}個のファイルを作成")

        return output_files

    except Exception as e:
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
    print("Juniper Syslog Filter - 列削減モジュール")
    print("=" * 60)

    try:
        # 入力CSVファイルを取得
        csv_files = sorted(input_dir.glob("*.csv"))

        if not csv_files:
            print(f"\n⚠️  CSVファイルが見つかりませんでした: {input_dir}")
            return 0

        print(f"\n対象ファイル数: {len(csv_files)}")
        print(f"保持する列: [0, 1, 2, 6] (Timestamp, Hostname, AppName, Message)")
        print()

        output_files = reduce_columns(
            csv_files, output_dir, keep_columns=[0, 1, 2, 6], verbose=True
        )

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
