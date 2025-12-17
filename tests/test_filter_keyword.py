"""
test_filter_keyword.py - filter_keyword.pyモジュールのテストコード
"""

import pytest
import csv
from pathlib import Path
import tempfile

from modules.filter_keyword import filter_csv_by_keyword, filter_keyword, FilterError


@pytest.fixture
def temp_dirs():
    """テスト用の一時ディレクトリを作成"""
    with tempfile.TemporaryDirectory() as input_dir, \
         tempfile.TemporaryDirectory() as output_dir:
        yield Path(input_dir), Path(output_dir)


@pytest.fixture
def sample_csv_with_attacks():
    """RT_IDP_ATTACKを含むサンプルCSVデータ"""
    return [
        ["Timestamp", "Hostname", "AppName", "SeverityLevel", "Severity", "LogType", "Message"],
        ["2025-12-16T00:11:01Z", "srx-fw01", "RT_IDP", "4", "WARNING", "THREAT", "RT_IDP_ATTACK_LOG: Malware detected"],
        ["2025-12-16T00:47:21Z", "srx-fw01", "RT_FLOW", "6", "INFO", "NORMAL", "RT_FLOW_SESSION_CLOSE: session closed"],
        ["2025-12-16T00:16:22Z", "srx-fw01", "RT_IDP", "2", "CRITICAL", "THREAT", "RT_IDP_ATTACK_LOG: Port scan detected"],
        ["2025-12-16T00:30:10Z", "srx-fw01", "RT_SCREEN", "4", "WARNING", "THREAT", "RT_SCREEN_UDP: UDP flood detected"],
    ]


def create_test_csv(path: Path, data: list):
    """テスト用のCSVファイルを作成"""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)


# ============================================================================
# filter_csv_by_keyword 関数のテスト
# ============================================================================

def test_filter_csv_by_keyword_success(temp_dirs, sample_csv_with_attacks):
    """正常なフィルタリングのテスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "test.csv"
    output_path = output_dir / "filtered.csv"
    
    # テストCSVを作成
    create_test_csv(input_path, sample_csv_with_attacks)
    
    # フィルタリング実行
    filtered_count = filter_csv_by_keyword(input_path, output_path, "RT_IDP_ATTACK")
    
    # 検証: RT_IDP_ATTACKを含む2行が抽出される
    assert filtered_count == 2
    assert output_path.exists()
    
    # 出力ファイルの内容を確認
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 3  # ヘッダー + 2行
        assert "RT_IDP_ATTACK" in rows[1][6]
        assert "RT_IDP_ATTACK" in rows[2][6]


def test_filter_csv_by_keyword_no_matches(temp_dirs):
    """キーワードが見つからない場合のテスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "test.csv"
    output_path = output_dir / "filtered.csv"
    
    csv_data = [
        ["Timestamp", "Hostname", "AppName", "SeverityLevel", "Severity", "LogType", "Message"],
        ["2025-12-16T00:47:21Z", "srx-fw01", "RT_FLOW", "6", "INFO", "NORMAL", "RT_FLOW_SESSION_CLOSE: session closed"],
    ]
    create_test_csv(input_path, csv_data)
    
    # フィルタリング実行
    filtered_count = filter_csv_by_keyword(input_path, output_path, "RT_IDP_ATTACK")
    
    # 検証: 0行が抽出される
    assert filtered_count == 0
    assert output_path.exists()


def test_filter_csv_by_keyword_file_not_found(temp_dirs):
    """存在しないファイルのテスト"""
    input_dir, output_dir = temp_dirs
    input_path = input_dir / "nonexistent.csv"
    output_path = output_dir / "filtered.csv"
    
    with pytest.raises(FileNotFoundError):
        filter_csv_by_keyword(input_path, output_path, "RT_IDP_ATTACK")


# ============================================================================
# filter_keyword 関数のテスト
# ============================================================================

def test_filter_keyword_multiple_files(temp_dirs, sample_csv_with_attacks):
    """複数ファイルのフィルタリングテスト"""
    input_dir, output_dir = temp_dirs
    
    # 3つのテストCSVを作成
    csv_files = []
    for i in range(3):
        csv_path = input_dir / f"test_{i:02d}.csv"
        create_test_csv(csv_path, sample_csv_with_attacks)
        csv_files.append(csv_path)
    
    # フィルタリング実行
    total_filtered = filter_keyword(csv_files, output_dir, keyword="RT_IDP_ATTACK", verbose=False)
    
    # 検証: 3ファイル × 2行 = 6行
    assert total_filtered == 6
    
    # 出力ファイルが3つ作成されている
    output_files = list(output_dir.glob("*.csv"))
    assert len(output_files) == 3


def test_filter_keyword_no_files(temp_dirs):
    """CSVファイルが無い場合のテスト"""
    input_dir, output_dir = temp_dirs
    
    total_filtered = filter_keyword([], output_dir, keyword="RT_IDP_ATTACK", verbose=False)
    
    # 検証: 0行が返る
    assert total_filtered == 0


# ============================================================================
# 実行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])