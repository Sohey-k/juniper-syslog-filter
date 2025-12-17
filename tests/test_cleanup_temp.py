"""
test_cleanup_temp.py - cleanup_temp.pyモジュールのテストコード
"""

import pytest
import zipfile
from pathlib import Path
import tempfile

from modules.cleanup_temp import (
    cleanup_processed_files,
    cleanup_directory,
    CleanupError,
)


@pytest.fixture
def temp_dirs():
    """テスト用の一時ディレクトリを作成"""
    with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as temp_dir:
        yield Path(source_dir), Path(temp_dir)


def create_test_files(directory: Path, filenames: list):
    """テスト用のファイルを作成"""
    for filename in filenames:
        file_path = directory / filename
        file_path.write_text("test content")


# ============================================================================
# cleanup_processed_files 関数のテスト
# ============================================================================


def test_cleanup_processed_files_success(temp_dirs):
    """正常なクリーンアップのテスト"""
    source_dir, temp_dir = temp_dirs

    # テストファイルを作成
    zip_path = source_dir / "test.zip"
    csv_path_1 = temp_dir / "test_1.csv"
    csv_path_2 = temp_dir / "test_2.csv"

    zip_path.write_text("test zip content")
    csv_path_1.write_text("test csv 1")
    csv_path_2.write_text("test csv 2")

    csv_files = [csv_path_1, csv_path_2]

    # クリーンアップ実行
    result = cleanup_processed_files(zip_path, csv_files, verbose=False)

    # 検証: 全て削除されている
    assert result is True
    assert not zip_path.exists()
    assert not csv_path_1.exists()
    assert not csv_path_2.exists()


def test_cleanup_processed_files_zip_not_found(temp_dirs):
    """ZIPファイルが存在しない場合のテスト"""
    source_dir, temp_dir = temp_dirs

    zip_path = source_dir / "nonexistent.zip"
    csv_path = temp_dir / "test.csv"
    csv_path.write_text("test content")

    csv_files = [csv_path]

    # クリーンアップ実行
    result = cleanup_processed_files(zip_path, csv_files, verbose=False)

    # 検証: Falseが返る（CSVは削除される）
    assert result is False
    assert not csv_path.exists()


def test_cleanup_processed_files_empty_list(temp_dirs):
    """CSVファイルリストが空の場合のテスト"""
    source_dir, temp_dir = temp_dirs

    zip_path = source_dir / "test.zip"
    zip_path.write_text("test content")

    # クリーンアップ実行
    result = cleanup_processed_files(zip_path, [], verbose=False)

    # 検証: ZIPだけ削除される
    assert result is True
    assert not zip_path.exists()


# ============================================================================
# cleanup_directory 関数のテスト
# ============================================================================


def test_cleanup_directory_success(temp_dirs):
    """ディレクトリクリーンアップのテスト"""
    source_dir, temp_dir = temp_dirs

    # テストファイルを作成
    create_test_files(temp_dir, ["test_1.csv", "test_2.csv", "test_3.txt"])

    # CSVファイルのみクリーンアップ
    deleted_count = cleanup_directory(temp_dir, "*.csv", verbose=False)

    # 検証: 2つのCSVファイルが削除される
    assert deleted_count == 2
    assert not (temp_dir / "test_1.csv").exists()
    assert not (temp_dir / "test_2.csv").exists()
    assert (temp_dir / "test_3.txt").exists()  # TXTは残る


def test_cleanup_directory_not_exist(temp_dirs):
    """存在しないディレクトリのテスト"""
    nonexistent_dir = Path("/nonexistent/directory")

    # エラーにならず0を返す
    deleted_count = cleanup_directory(nonexistent_dir, verbose=False)

    assert deleted_count == 0


# ============================================================================
# 実行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
