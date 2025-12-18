"""
test_extract.py - extract.pyのテストコード

ZIP展開機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import pandas.testing as pdt
import zipfile
import csv
from pathlib import Path
from modules.extract import extract_zip, extract_all_zips, ExtractError


@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリのフィクスチャ"""
    return tmp_path


def create_test_csv(csv_path: Path, rows: list):
    """テスト用CSVファイルを作成"""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
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
        writer.writerows(rows)


def create_test_zip(zip_path: Path, csv_filename: str, rows: list):
    """テスト用ZIPファイルを作成"""
    csv_path = zip_path.parent / csv_filename
    create_test_csv(csv_path, rows)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, arcname=csv_filename)

    csv_path.unlink()  # 元のCSVは削除


class TestExtractZip:
    """extract_zip関数のテスト"""

    def test_extract_single_csv(self, temp_dir):
        """正常系: 単一CSVファイルの展開"""
        # テストデータ作成
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "RT_IDP_ATTACK_LOG: SQL injection detected",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_FLOW",
                6,
                "INFO",
                "NORMAL",
                "RT_FLOW_SESSION_CREATE: session created",
            ],
        ]

        zip_path = temp_dir / "test.zip"
        output_dir = temp_dir / "output"
        create_test_zip(zip_path, "test.csv", rows)

        # 実行
        result = extract_zip(zip_path, output_dir)

        # 検証: List[Path]が返される
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].exists()

        # 出力されたCSVの内容を検証
        df = pd.read_csv(result[0])
        assert len(df) == 2
        assert df.iloc[0]["Message"] == "RT_IDP_ATTACK_LOG: SQL injection detected"

    def test_extract_multiple_csv(self, temp_dir):
        """正常系: 複数CSVファイルの展開"""
        rows1 = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "RT_IDP_ATTACK_LOG: SQL injection detected",
            ]
        ]
        rows2 = [
            [
                "2025-12-16T01:00:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "RT_IDP_ATTACK_LOG: Port scan detected",
            ]
        ]

        # 2つのCSVを含むZIPを作成
        csv_path1 = temp_dir / "test1.csv"
        csv_path2 = temp_dir / "test2.csv"
        create_test_csv(csv_path1, rows1)
        create_test_csv(csv_path2, rows2)

        zip_path = temp_dir / "multi.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(csv_path1, arcname="test1.csv")
            zf.write(csv_path2, arcname="test2.csv")

        csv_path1.unlink()
        csv_path2.unlink()

        # 実行
        result = extract_zip(zip_path, temp_dir / "output")

        # 検証: 2つのCSVが出力される
        assert len(result) == 2
        assert all(f.exists() for f in result)

    def test_extract_corrupted_zip(self, temp_dir):
        """異常系: 破損したZIPファイル"""
        zip_path = temp_dir / "corrupted.zip"
        zip_path.write_text("This is not a valid ZIP file")

        # 実行 & 検証
        with pytest.raises(ExtractError, match="破損したZIPファイルです"):
            extract_zip(zip_path, temp_dir / "output")

    def test_extract_non_existent_file(self, temp_dir):
        """異常系: 存在しないファイル"""
        zip_path = temp_dir / "non_existent.zip"

        # 実行 & 検証
        with pytest.raises(FileNotFoundError, match="ZIPファイルが見つかりません"):
            extract_zip(zip_path, temp_dir / "output")
