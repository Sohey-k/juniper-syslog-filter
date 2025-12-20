"""
test_filter_critical.py - filter_critical.py のテストコード
"""

import pytest
from pathlib import Path
import pandas as pd
from modules.filter_critical import filter_critical, FilterCriticalError


@pytest.fixture
def temp_csv_with_severity(tmp_path):
    """Severity列を含むテスト用CSVファイルを作成"""
    csv_path = tmp_path / "test_severity.csv"

    data = {
        "Timestamp": [
            "2025-01-01T10:00:00Z",
            "2025-01-01T10:01:00Z",
            "2025-01-01T10:02:00Z",
        ],
        "Hostname": ["srx-fw01", "srx-fw01", "srx-fw01"],
        "AppName": ["RT_IDP", "RT_IDP", "RT_IDP"],
        "Severity": ["CRITICAL", "WARNING", "CRITICAL"],
        "Message": ["Attack 1", "Attack 2", "Attack 3"],
    }

    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    return csv_path


@pytest.fixture
def temp_csv_warning_only(tmp_path):
    """WARNING行のみのテスト用CSVファイルを作成"""
    csv_path = tmp_path / "test_warning.csv"

    data = {
        "Timestamp": ["2025-01-01T10:00:00Z", "2025-01-01T10:01:00Z"],
        "Hostname": ["srx-fw01", "srx-fw01"],
        "AppName": ["RT_IDP", "RT_IDP"],
        "Severity": ["WARNING", "WARNING"],
        "Message": ["Attack 1", "Attack 2"],
    }

    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    return csv_path


@pytest.fixture
def temp_csv_no_severity(tmp_path):
    """Severity列がないテスト用CSVファイルを作成"""
    csv_path = tmp_path / "test_no_severity.csv"

    data = {
        "Timestamp": ["2025-01-01T10:00:00Z"],
        "Hostname": ["srx-fw01"],
        "Message": ["Test"],
    }

    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    return csv_path


def test_filter_critical_basic(temp_csv_with_severity, tmp_path):
    """基本的なCRITICAL行フィルタが正しく動作する"""
    output_dir = tmp_path / "output"

    result = filter_critical([temp_csv_with_severity], output_dir, verbose=False)

    # ファイルが1つ出力される
    assert len(result) == 1

    # 出力ファイルが存在する
    assert result[0].exists()

    # CRITICAL行のみが抽出されている
    df = pd.read_csv(result[0], encoding="utf-8")
    assert len(df) == 2  # CRITICAL行は2行
    assert all(df["Severity"] == "CRITICAL")
    assert list(df["Message"]) == ["Attack 1", "Attack 3"]


def test_filter_critical_multiple_files(temp_csv_with_severity, tmp_path):
    """複数ファイルを個別に処理できる"""
    # 2つ目のファイルを作成
    csv_path2 = tmp_path / "test_severity2.csv"
    data = {
        "Timestamp": ["2025-01-01T11:00:00Z", "2025-01-01T11:01:00Z"],
        "Hostname": ["srx-fw02", "srx-fw02"],
        "AppName": ["RT_IDP", "RT_IDP"],
        "Severity": ["CRITICAL", "INFO"],
        "Message": ["Attack 4", "Attack 5"],
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path2, index=False, encoding="utf-8")

    output_dir = tmp_path / "output"

    # 2つのファイルを処理
    result = filter_critical(
        [temp_csv_with_severity, csv_path2], output_dir, verbose=False
    )

    # 2つのファイルが出力される
    assert len(result) == 2

    # ファイル1: CRITICAL 2行
    df1 = pd.read_csv(result[0], encoding="utf-8")
    assert len(df1) == 2
    assert all(df1["Severity"] == "CRITICAL")

    # ファイル2: CRITICAL 1行
    df2 = pd.read_csv(result[1], encoding="utf-8")
    assert len(df2) == 1
    assert all(df2["Severity"] == "CRITICAL")


def test_filter_critical_no_critical_rows(temp_csv_warning_only, tmp_path):
    """CRITICAL行がない場合は空リストを返す"""
    output_dir = tmp_path / "output"

    result = filter_critical([temp_csv_warning_only], output_dir, verbose=False)

    # 空リストが返される
    assert result == []

    # 出力ファイルは作成されない
    assert len(list(output_dir.glob("*.csv"))) == 0


def test_filter_critical_missing_severity_column(temp_csv_no_severity, tmp_path):
    """Severity列がない場合はエラーを発生させる"""
    output_dir = tmp_path / "output"

    with pytest.raises(FilterCriticalError) as exc_info:
        filter_critical([temp_csv_no_severity], output_dir, verbose=False)

    assert "Severity列が見つかりません" in str(exc_info.value)
