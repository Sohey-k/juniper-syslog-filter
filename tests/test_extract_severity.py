"""
test_extract_severity.py - extract_severity.pyのテストコード

Severity抽出機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import csv
from pathlib import Path
from modules.extract_severity import extract_severity, ExtractSeverityError


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
                "routing",
                "srcIP",
                "srcIP_type",
                "dstIP",
                "dstIP_type",
                "protocol",
                "SeverityLevel",
                "Message",
            ]
        )
        writer.writerows(rows)


class TestExtractSeverity:
    """extract_severity関数のテスト"""

    def test_extract_severity_basic(self, temp_dir):
        """正常系: Severity情報が正しく抽出される"""
        # テストデータ作成
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.5 > 8.8.8.8",
                "192.168.1.5",
                "private",
                "8.8.8.8",
                "global",
                "tcp",
                "4",
                "RT_IDP_ATTACK_LOG: SQL injection protocol=tcp SeverityLevel=4 Severity=WARNING",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.1 > 1.1.1.1",
                "10.0.0.1",
                "private",
                "1.1.1.1",
                "global",
                "udp",
                "2",
                "RT_IDP_ATTACK_LOG: Port scan protocol=udp SeverityLevel=2 Severity=CRITICAL",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        result = extract_severity([input_path], output_dir, verbose=False)

        # 検証: ファイルが作成される
        assert len(result) == 1
        assert result[0].exists()

        # 出力ファイルの内容を検証
        df = pd.read_csv(result[0], keep_default_na=False)
        assert "Severity" in df.columns
        assert df.iloc[0]["Severity"] == "WARNING"
        assert df.iloc[1]["Severity"] == "CRITICAL"

        # 列の順序を確認（Severity は Message の直前）
        cols = df.columns.tolist()
        assert cols.index("Severity") == cols.index("Message") - 1

    def test_extract_severity_no_match(self, temp_dir):
        """正常系: Severity情報がない行は空文字列"""
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_FLOW",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "RT_FLOW_SESSION_CREATE: session created",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.5 > 8.8.8.8",
                "192.168.1.5",
                "private",
                "8.8.8.8",
                "global",
                "tcp",
                "3",
                "RT_IDP_ATTACK_LOG: attack detected protocol=tcp SeverityLevel=3 Severity=INFO",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        result = extract_severity([input_path], output_dir, verbose=False)

        # 検証
        df = pd.read_csv(result[0], keep_default_na=False)
        assert df.iloc[0]["Severity"] == ""  # Severity情報なし
        assert df.iloc[1]["Severity"] == "INFO"  # Severity情報あり

    def test_extract_severity_multiple_files(self, temp_dir):
        """正常系: 複数ファイルの処理"""
        rows1 = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.1 > 8.8.8.8",
                "192.168.1.1",
                "private",
                "8.8.8.8",
                "global",
                "tcp",
                "5",
                "Test protocol=tcp SeverityLevel=5 Severity=WARNING data",
            ]
        ]
        rows2 = [
            [
                "2025-12-16T01:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "10.0.0.1 > 1.1.1.1",
                "10.0.0.1",
                "private",
                "1.1.1.1",
                "global",
                "udp",
                "1",
                "Test protocol=udp SeverityLevel=1 Severity=CRITICAL data",
            ]
        ]

        input_path1 = temp_dir / "test1.csv"
        input_path2 = temp_dir / "test2.csv"
        output_dir = temp_dir / "output"

        create_test_csv(input_path1, rows1)
        create_test_csv(input_path2, rows2)

        # 実行
        result = extract_severity([input_path1, input_path2], output_dir, verbose=False)

        # 検証: 2ファイルが処理される
        assert len(result) == 2

        df1 = pd.read_csv(result[0], keep_default_na=False)
        df2 = pd.read_csv(result[1], keep_default_na=False)
        assert df1.iloc[0]["Severity"] == "WARNING"
        assert df2.iloc[0]["Severity"] == "CRITICAL"

    def test_extract_severity_missing_message_column(self, temp_dir):
        """異常系: Message列が存在しない場合はエラー"""
        # Message列がないCSVを作成
        csv_path = temp_dir / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Hostname"])
            writer.writerow(["2025-12-16T00:00:00Z", "srx-fw01"])

        output_dir = temp_dir / "output"

        # 実行 & 検証
        with pytest.raises(ExtractSeverityError, match="Message列が見つかりません"):
            extract_severity([csv_path], output_dir, verbose=False)
