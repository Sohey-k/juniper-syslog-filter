"""
test_reduce_columns.py - reduce_columns.pyモジュールのテストコード
"""

import pytest
import csv
from pathlib import Path
import tempfile

from modules.reduce_columns import (
    reduce_csv_columns,
    reduce_columns,
    ReduceColumnsError,
)


@pytest.fixture
def temp_dirs():
    """テスト用の一時ディレクトリを作成"""
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
        yield Path(input_dir), Path(output_dir)


def create_test_csv(path: Path, row_count: int = 5):
    """テスト用のCSVファイルを作成"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # ヘッダー（7列）
        writer.writerow(
            [
                "Timestamp",
                "Hostname",
                "AppName",
                "SeverityLevel",
                "Severity",
                "LogType",
                "Message",
            ]
        )
        # データ行
        for i in range(row_count):
            writer.writerow(
                [
                    f"2025-12-16T00:00:{i:02d}Z",
                    "srx-fw01",
                    "RT_IDP",
                    "2",
                    "CRITICAL",
                    "THREAT",
                    f"RT_IDP_ATTACK_LOG: Attack {i}",
                ]
            )


# ============================================================================
# reduce_csv_columns 関数のテスト
# ============================================================================


def test_reduce_csv_columns_default(temp_dirs):
    """デフォルト列削減のテスト（Timestamp, Hostname, AppName, Message）"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "test.csv"
    output_path = output_dir / "reduced.csv"

    # テストCSVを作成
    create_test_csv(input_path, row_count=3)

    # 列削減実行（デフォルト: [0, 1, 2, 6]）
    row_count = reduce_csv_columns(input_path, output_path, keep_columns=[0, 1, 2, 6])

    # 検証: 4行処理（ヘッダー + 3行）
    assert row_count == 4
    assert output_path.exists()

    # 出力ファイルの内容を確認
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # ヘッダー確認（4列）
        assert len(rows[0]) == 4
        assert rows[0] == ["Timestamp", "Hostname", "AppName", "Message"]

        # データ行確認（4列）
        assert len(rows[1]) == 4
        assert rows[1][0].startswith("2025-12-16")
        assert rows[1][1] == "srx-fw01"
        assert rows[1][2] == "RT_IDP"
        assert "RT_IDP_ATTACK_LOG" in rows[1][3]


def test_reduce_csv_columns_custom(temp_dirs):
    """カスタム列削減のテスト（Timestamp と Message のみ）"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "test.csv"
    output_path = output_dir / "reduced.csv"

    # テストCSVを作成
    create_test_csv(input_path, row_count=2)

    # 列削減実行（カスタム: [0, 6]）
    row_count = reduce_csv_columns(input_path, output_path, keep_columns=[0, 6])

    # 検証: 3行処理（ヘッダー + 2行）
    assert row_count == 3

    # 出力ファイルの内容を確認
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # ヘッダー確認（2列）
        assert len(rows[0]) == 2
        assert rows[0] == ["Timestamp", "Message"]

        # データ行確認（2列）
        assert len(rows[1]) == 2


def test_reduce_csv_columns_file_not_found(temp_dirs):
    """存在しないファイルのテスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "nonexistent.csv"
    output_path = output_dir / "reduced.csv"

    with pytest.raises(FileNotFoundError):
        reduce_csv_columns(input_path, output_path, keep_columns=[0, 1, 2, 6])


# ============================================================================
# reduce_columns 関数のテスト
# ============================================================================


def test_reduce_columns_multiple_files(temp_dirs):
    """複数ファイルの列削減テスト"""
    input_dir, output_dir = temp_dirs

    # 3つのテストCSVを作成
    input_files = []
    for i in range(3):
        csv_path = input_dir / f"test_{i:02d}.csv"
        create_test_csv(csv_path, row_count=5)
        input_files.append(csv_path)

    # 列削減実行
    output_files = reduce_columns(
        input_files, output_dir, keep_columns=[0, 1, 2, 6], verbose=False
    )

    # 検証: 3ファイル作成
    assert len(output_files) == 3

    # 各ファイルが4列になっているか確認
    for output_file in output_files:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert len(header) == 4


def test_reduce_columns_empty_list(temp_dirs):
    """入力ファイルが空の場合のテスト"""
    input_dir, output_dir = temp_dirs

    output_files = reduce_columns([], output_dir, verbose=False)

    # 検証: 空のリストが返る
    assert output_files == []


# ============================================================================
# 実行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
