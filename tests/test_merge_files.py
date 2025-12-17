"""
test_merge_files.py - merge_files.pyモジュールのテストコード
"""

import pytest
import csv
from pathlib import Path
import tempfile

from modules.merge_files import merge_csv_files, MergeError


@pytest.fixture
def temp_dirs():
    """テスト用の一時ディレクトリを作成"""
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
        yield Path(input_dir), Path(output_dir)


def create_test_csv(path: Path, row_count: int):
    """テスト用のCSVファイルを作成"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # ヘッダー
        writer.writerow(["Timestamp", "Hostname", "AppName", "Message"])
        # データ行
        for i in range(row_count):
            writer.writerow(
                [f"2025-12-16T00:00:{i:02d}Z", "srx-fw01", "RT_IDP", f"Message {i}"]
            )


# ============================================================================
# merge_csv_files 関数のテスト
# ============================================================================


def test_merge_csv_files_small_files(temp_dirs):
    """小さいファイルのマージテスト（1ファイルに収まる）"""
    input_dir, output_dir = temp_dirs

    # 3つの小さいCSVを作成（合計300行）
    input_files = []
    for i in range(3):
        csv_path = input_dir / f"test_{i:02d}.csv"
        create_test_csv(csv_path, 100)
        input_files.append(csv_path)

    # マージ実行（max_rows=1000）
    output_files = merge_csv_files(
        input_files, output_dir, max_rows=1000, verbose=False
    )

    # 検証: 1ファイルにまとまる
    assert len(output_files) == 1
    assert output_files[0].name == "merged_001.csv"

    # 行数確認（ヘッダー + 300行）
    with open(output_files[0], "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
        assert len(rows) == 301  # ヘッダー + 300行


def test_merge_csv_files_split(temp_dirs):
    """ファイル分割のテスト（max_rowsを超える場合）"""
    input_dir, output_dir = temp_dirs

    # 2つのCSVを作成（合計200行）
    input_files = []
    for i in range(2):
        csv_path = input_dir / f"test_{i:02d}.csv"
        create_test_csv(csv_path, 100)
        input_files.append(csv_path)

    # マージ実行（max_rows=150で分割される）
    output_files = merge_csv_files(input_files, output_dir, max_rows=150, verbose=False)

    # 検証: 2ファイルに分割される
    assert len(output_files) == 2
    assert output_files[0].name == "merged_001.csv"
    assert output_files[1].name == "merged_002.csv"

    # 1つ目のファイル: 150行
    with open(output_files[0], "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
        assert len(rows) == 151  # ヘッダー + 150行

    # 2つ目のファイル: 50行
    with open(output_files[1], "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
        assert len(rows) == 51  # ヘッダー + 50行


def test_merge_csv_files_empty_list(temp_dirs):
    """入力ファイルが空の場合のテスト"""
    input_dir, output_dir = temp_dirs

    output_files = merge_csv_files([], output_dir, verbose=False)

    # 検証: 空のリストが返る
    assert output_files == []


def test_merge_csv_files_file_not_found(temp_dirs):
    """存在しないファイルのテスト"""
    input_dir, output_dir = temp_dirs

    nonexistent_file = input_dir / "nonexistent.csv"

    with pytest.raises(MergeError):
        merge_csv_files([nonexistent_file], output_dir, verbose=False)


# ============================================================================
# 実行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
