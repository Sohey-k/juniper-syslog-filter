"""
test_merge_files.py - merge_files.pyのテストコード

CSVマージ機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import csv
from pathlib import Path
from modules.merge_files import merge_csv_files, MergeError


@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリのフィクスチャ"""
    return tmp_path


def create_test_csv(csv_path: Path, row_count: int):
    """テスト用CSVファイルを作成（指定行数）"""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Hostname", "AppName", "Message"])

        for i in range(row_count):
            writer.writerow(
                [
                    f"2025-12-16T{i % 24:02d}:00:00Z",
                    "srx-fw01",
                    "RT_IDP",
                    f"RT_IDP_ATTACK_LOG: Test message {i}",
                ]
            )


class TestMergeCsvFiles:
    """merge_csv_files関数のテスト"""

    def test_merge_multiple_files_under_limit(self, temp_dir):
        """正常系: 複数ファイルをマージ（80万行以下）"""
        # 3つのCSVファイルを作成（各100行）
        input_files = []
        for i in range(3):
            csv_path = temp_dir / f"test{i}.csv"
            create_test_csv(csv_path, 100)
            input_files.append(csv_path)

        output_dir = temp_dir / "output"

        # 実行
        result = merge_csv_files(
            input_files, output_dir, max_rows=800000, verbose=False
        )

        # 検証: 1つのマージファイルが作成される
        assert len(result) == 1
        assert result[0].exists()

        # マージされたファイルの内容を確認
        df = pd.read_csv(result[0])
        assert len(df) == 300  # 100行 × 3ファイル

    def test_merge_split_over_limit(self, temp_dir):
        """正常系: 80万行超えで分割される"""
        # 2つのCSVファイルを作成（合計で制限を超える）
        csv_path1 = temp_dir / "test1.csv"
        csv_path2 = temp_dir / "test2.csv"
        create_test_csv(csv_path1, 600)
        create_test_csv(csv_path2, 600)

        input_files = [csv_path1, csv_path2]
        output_dir = temp_dir / "output"

        # 実行（max_rows=1000で分割）
        result = merge_csv_files(input_files, output_dir, max_rows=1000, verbose=False)

        # 検証: 2つのファイルに分割される（1200行 → 1000行 + 200行）
        assert len(result) == 2

        df1 = pd.read_csv(result[0])
        df2 = pd.read_csv(result[1])
        assert len(df1) == 1000
        assert len(df2) == 200

    def test_merge_skip_empty_files(self, temp_dir):
        """正常系: 空ファイルはスキップされる"""
        # 通常のファイルと空のファイルを作成
        csv_path1 = temp_dir / "test1.csv"
        csv_path2 = temp_dir / "empty.csv"
        csv_path3 = temp_dir / "test3.csv"

        create_test_csv(csv_path1, 50)
        csv_path2.write_text("")  # 空ファイル
        create_test_csv(csv_path3, 50)

        input_files = [csv_path1, csv_path2, csv_path3]
        output_dir = temp_dir / "output"

        # 実行（空ファイルはスキップされる）
        result = merge_csv_files(input_files, output_dir, verbose=False)

        # 検証: 100行のマージファイルが作成される（50 + 50）
        assert len(result) == 1
        df = pd.read_csv(result[0])
        assert len(df) == 100

    def test_merge_empty_input_list(self, temp_dir):
        """正常系: 入力ファイルが空リストの場合は空リストを返す"""
        output_dir = temp_dir / "output"

        # 実行
        result = merge_csv_files([], output_dir, verbose=False)

        # 検証: 空リスト
        assert result == []

        # 出力ファイルも作成されない
        assert not list(output_dir.glob("*.csv"))
