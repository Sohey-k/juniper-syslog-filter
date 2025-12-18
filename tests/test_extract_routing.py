"""
test_extract_routing.py - extract_routing.pyのテストコード

routing抽出機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import csv
from pathlib import Path
from modules.extract_routing import extract_routing, ExtractRoutingError


@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリのフィクスチャ"""
    return tmp_path


def create_test_csv(csv_path: Path, rows: list):
    """テスト用CSVファイルを作成"""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Hostname", "AppName", "Message"])
        writer.writerows(rows)


class TestExtractRouting:
    """extract_routing関数のテスト"""

    def test_extract_routing_basic(self, temp_dir):
        """正常系: routing情報が正しく抽出される"""
        # テストデータ作成
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "RT_IDP_ATTACK_LOG: SQL injection 192.168.1.5/12345 > 203.0.113.10/80 protocol=tcp",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "RT_IDP_ATTACK_LOG: Port scan 10.0.0.100/54321 > 8.8.8.8/443 protocol=tcp",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        result = extract_routing([input_path], output_dir, verbose=False)

        # 検証: ファイルが作成される
        assert len(result) == 1
        assert result[0].exists()

        # 出力ファイルの内容を検証
        df = pd.read_csv(result[0], keep_default_na=False)
        assert "routing" in df.columns
        assert df.iloc[0]["routing"] == "192.168.1.5 > 203.0.113.10"
        assert df.iloc[1]["routing"] == "10.0.0.100 > 8.8.8.8"

        # 列の順序を確認（routing は Message の前）
        cols = df.columns.tolist()
        assert cols.index("routing") < cols.index("Message")

    def test_extract_routing_no_match(self, temp_dir):
        """正常系: routing情報がない行は空文字列"""
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_FLOW",
                "RT_FLOW_SESSION_CREATE: session created",
            ],
            [
                "2025-12-16T00:01:00Z",
                "srx-fw01",
                "RT_IDP",
                "RT_IDP_ATTACK_LOG: SQL injection 192.168.1.5/12345 > 203.0.113.10/80 protocol=tcp",
            ],
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行
        result = extract_routing([input_path], output_dir, verbose=False)

        # 検証（keep_default_na=Falseで空文字列をNaNにしない）
        df = pd.read_csv(result[0], keep_default_na=False)
        assert df.iloc[0]["routing"] == ""  # routing情報なし
        assert df.iloc[1]["routing"] == "192.168.1.5 > 203.0.113.10"  # routing情報あり

    def test_extract_routing_multiple_files(self, temp_dir):
        """正常系: 複数ファイルの処理"""
        rows1 = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "Test 192.168.1.1/1111 > 8.8.8.8/80 data",
            ]
        ]
        rows2 = [
            [
                "2025-12-16T01:00:00Z",
                "srx-fw01",
                "RT_IDP",
                "Test 10.0.0.1/2222 > 1.1.1.1/443 data",
            ]
        ]

        input_path1 = temp_dir / "test1.csv"
        input_path2 = temp_dir / "test2.csv"
        output_dir = temp_dir / "output"

        create_test_csv(input_path1, rows1)
        create_test_csv(input_path2, rows2)

        # 実行
        result = extract_routing([input_path1, input_path2], output_dir, verbose=False)

        # 検証: 2ファイルが処理される
        assert len(result) == 2

        df1 = pd.read_csv(result[0], keep_default_na=False)
        df2 = pd.read_csv(result[1], keep_default_na=False)
        assert df1.iloc[0]["routing"] == "192.168.1.1 > 8.8.8.8"
        assert df2.iloc[0]["routing"] == "10.0.0.1 > 1.1.1.1"

    def test_extract_routing_missing_message_column(self, temp_dir):
        """異常系: Message列が存在しない場合はエラー"""
        # Message列がないCSVを作成
        csv_path = temp_dir / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Hostname"])
            writer.writerow(["2025-12-16T00:00:00Z", "srx-fw01"])

        output_dir = temp_dir / "output"

        # 実行 & 検証
        with pytest.raises(ExtractRoutingError, match="Message列が見つかりません"):
            extract_routing([csv_path], output_dir, verbose=False)
