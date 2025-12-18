"""
test_reduce_columns.py - reduce_columns.pyのテストコード

列削減機能（pandas + ファイル出力版）をテスト
"""

import pytest
import pandas as pd
import csv
from pathlib import Path
from modules.reduce_columns import reduce_columns, ReduceColumnsError


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


class TestReduceColumns:
    """reduce_columns関数のテスト"""

    def test_reduce_columns_basic(self, temp_dir):
        """正常系: 列削減が正しく動作する"""
        # テストデータ作成（7列）
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

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行（列0,1,2,6のみ保持）
        result = reduce_columns(
            [input_path], output_dir, keep_columns=[0, 1, 2, 6], verbose=False
        )

        # 検証: ファイルが作成される
        assert len(result) == 1
        assert result[0].exists()

        # 出力ファイルの内容を検証
        df = pd.read_csv(result[0])
        assert len(df.columns) == 4  # 7列 → 4列
        assert list(df.columns) == ["Timestamp", "Hostname", "AppName", "Message"]
        assert len(df) == 2  # 行数は変わらない

    def test_reduce_columns_multiple_files(self, temp_dir):
        """正常系: 複数ファイルの処理"""
        rows1 = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "Message 1",
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
                "Message 2",
            ]
        ]

        input_path1 = temp_dir / "test1.csv"
        input_path2 = temp_dir / "test2.csv"
        output_dir = temp_dir / "output"

        create_test_csv(input_path1, rows1)
        create_test_csv(input_path2, rows2)

        # 実行
        result = reduce_columns(
            [input_path1, input_path2],
            output_dir,
            keep_columns=[0, 2, 6],
            verbose=False,
        )

        # 検証: 2ファイルが処理される
        assert len(result) == 2

        # 各ファイルの列数を確認
        df1 = pd.read_csv(result[0])
        df2 = pd.read_csv(result[1])
        assert len(df1.columns) == 3
        assert len(df2.columns) == 3

    def test_reduce_columns_invalid_index(self, temp_dir):
        """異常系: 範囲外の列インデックス"""
        rows = [
            [
                "2025-12-16T00:00:00Z",
                "srx-fw01",
                "RT_IDP",
                2,
                "CRITICAL",
                "THREAT",
                "Message",
            ]
        ]

        input_path = temp_dir / "test.csv"
        output_dir = temp_dir / "output"
        create_test_csv(input_path, rows)

        # 実行（列インデックス10は範囲外）
        with pytest.raises(ReduceColumnsError, match="列インデックス.*が範囲外です"):
            reduce_columns(
                [input_path], output_dir, keep_columns=[0, 1, 10], verbose=False
            )

    def test_reduce_columns_empty_input_list(self, temp_dir):
        """正常系: 入力が空リストの場合は空リストを返す"""
        output_dir = temp_dir / "output"

        # 実行
        result = reduce_columns([], output_dir, verbose=False)

        # 検証: 空リスト
        assert result == []
