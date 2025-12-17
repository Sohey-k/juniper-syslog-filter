"""
test_extract.py - extract.pyモジュールのテストコード
"""

import pytest
import zipfile
import csv
from pathlib import Path
import tempfile
import shutil

from modules.extract import extract_zip, extract_all_zips, ExtractError


@pytest.fixture
def temp_dirs():
    """テスト用の一時ディレクトリを作成"""
    with tempfile.TemporaryDirectory() as source_dir, \
         tempfile.TemporaryDirectory() as output_dir:
        yield Path(source_dir), Path(output_dir)


@pytest.fixture
def sample_csv_content():
    """サンプルCSVデータ"""
    return [
        ["Timestamp", "Hostname", "AppName", "SeverityLevel", "Severity", "LogType", "Message"],
        ["2025-12-16T00:00:00Z", "srx-fw01", "RT_IDP_ATTACK", "2", "CRITICAL", "THREAT", "Test log 1"],
        ["2025-12-16T00:01:00Z", "srx-fw01", "RT_IDP_ATTACK", "3", "WARNING", "THREAT", "Test log 2"],
    ]


def create_test_zip(zip_path: Path, csv_filename: str, csv_content: list):
    """テスト用のZIPファイルを作成"""
    csv_path = zip_path.parent / csv_filename
    
    # CSVファイルを作成
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_content)
    
    # ZIPファイルを作成
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(csv_path, csv_filename)
    
    # 元のCSVファイルを削除
    csv_path.unlink()


# ============================================================================
# extract_zip 関数のテスト
# ============================================================================

def test_extract_zip_success(temp_dirs, sample_csv_content):
    """正常なZIP展開のテスト"""
    source_dir, output_dir = temp_dirs
    zip_path = source_dir / "test.zip"
    
    # テストZIPを作成
    create_test_zip(zip_path, "test.csv", sample_csv_content)
    
    # ZIP展開
    extracted_files = extract_zip(zip_path, output_dir)
    
    # 検証
    assert len(extracted_files) == 1
    assert extracted_files[0].name == "test.csv"
    assert extracted_files[0].exists()
    
    # CSVの内容確認
    with open(extracted_files[0], 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0][0] == "Timestamp"


def test_extract_zip_file_not_found(temp_dirs):
    """存在しないZIPファイルのテスト"""
    source_dir, output_dir = temp_dirs
    zip_path = source_dir / "nonexistent.zip"
    
    with pytest.raises(FileNotFoundError):
        extract_zip(zip_path, output_dir)


def test_extract_zip_not_zip_file(temp_dirs):
    """ZIPでないファイルのテスト"""
    source_dir, output_dir = temp_dirs
    txt_path = source_dir / "test.txt"
    txt_path.write_text("This is not a zip file")
    
    with pytest.raises(ExtractError):
        extract_zip(txt_path, output_dir)


def test_extract_zip_empty_zip(temp_dirs):
    """空のZIPファイルのテスト"""
    source_dir, output_dir = temp_dirs
    zip_path = source_dir / "empty.zip"
    
    # 空のZIPファイルを作成
    with zipfile.ZipFile(zip_path, 'w'):
        pass
    
    with pytest.raises(ExtractError, match="ZIPファイルが空です"):
        extract_zip(zip_path, output_dir)


def test_extract_zip_no_csv(temp_dirs):
    """CSVファイルが含まれないZIPのテスト"""
    source_dir, output_dir = temp_dirs
    zip_path = source_dir / "no_csv.zip"
    txt_path = source_dir / "test.txt"
    
    # テキストファイルを作成
    txt_path.write_text("This is a text file")
    
    # ZIPファイルを作成
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(txt_path, "test.txt")
    
    txt_path.unlink()
    
    with pytest.raises(ExtractError, match="CSVファイルが見つかりませんでした"):
        extract_zip(zip_path, output_dir)


def test_extract_zip_corrupted(temp_dirs):
    """破損したZIPファイルのテスト"""
    source_dir, output_dir = temp_dirs
    zip_path = source_dir / "corrupted.zip"
    
    # 破損したZIPファイルを作成
    zip_path.write_bytes(b"This is not a valid zip file")
    
    with pytest.raises(ExtractError, match="破損したZIPファイルです"):
        extract_zip(zip_path, output_dir)


# ============================================================================
# extract_all_zips 関数のテスト
# ============================================================================

def test_extract_all_zips_success(temp_dirs, sample_csv_content):
    """複数ZIPファイルの展開テスト"""
    source_dir, output_dir = temp_dirs
    
    # 3つのテストZIPを作成
    for i in range(3):
        zip_path = source_dir / f"test_{i:02d}.zip"
        create_test_zip(zip_path, f"{i:02d}.csv", sample_csv_content)
    
    # 全ZIP展開
    extracted_files = extract_all_zips(source_dir, output_dir, verbose=False)
    
    # 検証
    assert len(extracted_files) == 3
    for i, file in enumerate(sorted(extracted_files)):
        assert file.name == f"{i:02d}.csv"
        assert file.exists()


def test_extract_all_zips_no_zips(temp_dirs):
    """ZIPファイルが無い場合のテスト"""
    source_dir, output_dir = temp_dirs
    
    extracted_files = extract_all_zips(source_dir, output_dir, verbose=False)
    
    # 検証: 空のリストが返る
    assert extracted_files == []


def test_extract_all_zips_source_not_exist():
    """ソースディレクトリが存在しない場合のテスト"""
    source_dir = Path("/nonexistent/directory")
    output_dir = Path("/tmp/output")
    
    with pytest.raises(FileNotFoundError):
        extract_all_zips(source_dir, output_dir, verbose=False)


def test_extract_all_zips_mixed_success_failure(temp_dirs, sample_csv_content):
    """成功と失敗が混在する場合のテスト"""
    source_dir, output_dir = temp_dirs
    
    # 正常なZIPファイル
    zip_path_1 = source_dir / "test_01.zip"
    create_test_zip(zip_path_1, "01.csv", sample_csv_content)
    
    # 破損したZIPファイル
    zip_path_2 = source_dir / "test_02.zip"
    zip_path_2.write_bytes(b"corrupted")
    
    # 正常なZIPファイル
    zip_path_3 = source_dir / "test_03.zip"
    create_test_zip(zip_path_3, "03.csv", sample_csv_content)
    
    # 全ZIP展開（エラーがあっても続行）
    extracted_files = extract_all_zips(source_dir, output_dir, verbose=False)
    
    # 検証: 2つの正常なファイルが展開される
    assert len(extracted_files) == 2


def test_extract_all_zips_verbose_output(temp_dirs, sample_csv_content, capsys):
    """詳細出力のテスト"""
    source_dir, output_dir = temp_dirs
    
    zip_path = source_dir / "test.zip"
    create_test_zip(zip_path, "test.csv", sample_csv_content)
    
    # verbose=True で実行
    extract_all_zips(source_dir, output_dir, verbose=True)
    
    captured = capsys.readouterr()
    assert "展開中" in captured.out
    assert "展開完了" in captured.out


# ============================================================================
# 実行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])