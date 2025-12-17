"""
test_classify_ip.py - classify_ip.pyモジュールのテストコード
"""

import pytest
import csv
from pathlib import Path
import tempfile

from modules.classify_ip import (
    is_private_ip,
    classify_ip_address,
    classify_ip_from_csv,
    classify_ip,
    ClassifyIPError,
)


@pytest.fixture
def temp_dirs():
    """テスト用の一時ディレクトリを作成"""
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
        yield Path(input_dir), Path(output_dir)


def create_test_csv(path: Path):
    """テスト用のCSVファイルを作成"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # ヘッダー
        writer.writerow(
            ["Timestamp", "Hostname", "AppName", "routing", "srcIP", "dstIP", "Message"]
        )
        # private → private
        writer.writerow(
            [
                "2025-12-16T00:11:01Z",
                "srx-fw01",
                "RT_IDP",
                "192.168.1.1 > 10.0.0.5",
                "192.168.1.1",
                "10.0.0.5",
                "RT_IDP_ATTACK_LOG: Attack",
            ]
        )
        # private → global
        writer.writerow(
            [
                "2025-12-16T00:16:22Z",
                "srx-fw01",
                "RT_IDP",
                "172.16.0.1 > 8.8.8.8",
                "172.16.0.1",
                "8.8.8.8",
                "RT_IDP_ATTACK_LOG: Scan",
            ]
        )
        # global → global
        writer.writerow(
            [
                "2025-12-16T00:20:00Z",
                "srx-fw01",
                "RT_IDP",
                "203.0.113.10 > 185.220.101.1",
                "203.0.113.10",
                "185.220.101.1",
                "RT_IDP_ATTACK_LOG: Traffic",
            ]
        )
        # 空のIP
        writer.writerow(
            [
                "2025-12-16T00:25:00Z",
                "srx-fw01",
                "RT_FLOW",
                "",
                "",
                "",
                "RT_FLOW_SESSION_CLOSE",
            ]
        )


# ============================================================================
# is_private_ip 関数のテスト
# ============================================================================


def test_is_private_ip_10_range():
    """10.x.x.x範囲のテスト"""
    assert is_private_ip("10.0.0.1") == True
    assert is_private_ip("10.255.255.254") == True
    assert is_private_ip("10.128.0.1") == True


def test_is_private_ip_172_range():
    """172.16-31.x.x範囲のテスト"""
    assert is_private_ip("172.16.0.1") == True
    assert is_private_ip("172.31.255.254") == True
    assert is_private_ip("172.20.0.1") == True
    # 範囲外
    assert is_private_ip("172.15.0.1") == False
    assert is_private_ip("172.32.0.1") == False


def test_is_private_ip_192_range():
    """192.168.x.x範囲のテスト"""
    assert is_private_ip("192.168.0.1") == True
    assert is_private_ip("192.168.255.254") == True
    assert is_private_ip("192.168.1.100") == True
    # 範囲外
    assert is_private_ip("192.167.0.1") == False
    assert is_private_ip("192.169.0.1") == False


def test_is_private_ip_global():
    """グローバルIPのテスト"""
    assert is_private_ip("8.8.8.8") == False
    assert is_private_ip("203.0.113.10") == False
    assert is_private_ip("185.220.101.1") == False


def test_is_private_ip_invalid():
    """無効なIPのテスト"""
    assert is_private_ip("") == False
    assert is_private_ip("invalid") == False
    assert is_private_ip("256.1.1.1") == False


# ============================================================================
# classify_ip_address 関数のテスト
# ============================================================================


def test_classify_ip_address():
    """IP分類のテスト"""
    assert classify_ip_address("192.168.1.1") == "private"
    assert classify_ip_address("10.0.0.5") == "private"
    assert classify_ip_address("172.16.0.1") == "private"
    assert classify_ip_address("8.8.8.8") == "global"
    assert classify_ip_address("203.0.113.10") == "global"
    assert classify_ip_address("") == ""


# ============================================================================
# classify_ip_from_csv 関数のテスト
# ============================================================================


def test_classify_ip_from_csv_success(temp_dirs):
    """CSVファイルからのIP分類テスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "test.csv"
    output_path = output_dir / "classified.csv"

    # テストCSVを作成
    create_test_csv(input_path)

    # IP分類実行
    row_count = classify_ip_from_csv(input_path, output_path, verbose=False)

    # 検証: 5行処理（ヘッダー + 4行）
    assert row_count == 5
    assert output_path.exists()

    # 出力ファイルの内容を確認
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # ヘッダー確認（9列）
        assert len(rows[0]) == 9
        assert rows[0][5] == "srcIP_type"
        assert rows[0][7] == "dstIP_type"

        # 1行目: private → private
        assert rows[1][5] == "private"  # srcIP_type
        assert rows[1][7] == "private"  # dstIP_type

        # 2行目: private → global
        assert rows[2][5] == "private"
        assert rows[2][7] == "global"

        # 3行目: global → global
        assert rows[3][5] == "global"
        assert rows[3][7] == "global"

        # 4行目: 空
        assert rows[4][5] == ""
        assert rows[4][7] == ""


def test_classify_ip_from_csv_file_not_found(temp_dirs):
    """存在しないファイルのテスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "nonexistent.csv"
    output_path = output_dir / "classified.csv"

    with pytest.raises(FileNotFoundError):
        classify_ip_from_csv(input_path, output_path, verbose=False)


# ============================================================================
# classify_ip 関数のテスト
# ============================================================================


def test_classify_ip_multiple_files(temp_dirs):
    """複数ファイルのIP分類テスト"""
    input_dir, output_dir = temp_dirs

    # 2つのテストCSVを作成
    input_files = []
    for i in range(2):
        csv_path = input_dir / f"test_{i:02d}.csv"
        create_test_csv(csv_path)
        input_files.append(csv_path)

    # IP分類実行
    output_files = classify_ip(input_files, output_dir, verbose=False)

    # 検証: 2ファイル作成
    assert len(output_files) == 2

    # 各ファイルが9列になっているか確認
    for output_file in output_files:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert len(header) == 9
            assert header[5] == "srcIP_type"
            assert header[7] == "dstIP_type"


def test_classify_ip_empty_list(temp_dirs):
    """入力ファイルが空の場合のテスト"""
    input_dir, output_dir = temp_dirs

    output_files = classify_ip([], output_dir, verbose=False)

    # 検証: 空のリストが返る
    assert output_files == []


# ============================================================================
# 実行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
