# Juniper Syslog フィルタリングツール - 設計書 v2.0

## 📋 プロジェクト概要

Windowsで動作するJuniper SRX syslogフィルタリングツール。  
大量のログファイル（ZIP圧縮された24時間分のCSV）から、特定条件でフィルタリングし、Excel形式で出力する。

**開発者**: Sohey-k  
**言語**: Python 3.x  
**対象OS**: Windows  
**リポジトリ**: https://github.com/Sohey-k/juniper-syslog-generator

---

## 🎯 プロジェクトの背景（Problem）

### 実務で直面した課題

元職場で、定期レポート用の脅威データをフィルタリングする業務がありました。  
使用されていたツールは **GUI操作を前提とした画像認識・座標指定型の自動化スクリプト** で作成されたものでしたが、以下の深刻な問題を抱えていました：

#### 旧スクリプトの問題点

| 問題                 | 詳細                                                     |
| -------------------- | -------------------------------------------------------- |
| **処理時間**         | 約2時間かかる                                            |
| **操作制限**         | スクリプト実行中、マウスを動かせない（座標ベースの操作） |
| **安定性**           | エラーハンドリングがなく、よく処理が止まる               |
| **スケーラビリティ** | 100万行以上のログでフリーズする                          |

オペレーターは「これが当たり前」として使用していましたが、明らかに改善の余地がありました。

---

## 💡 解決したアプローチ（Solution）

### Python ETLスクリプトへの移行

最初はVBAで実装を試みましたが、同様にフリーズが発生。  
そこで、実務未経験だったPythonを、GPTの支援を受けながら学習し、本格的なETLスクリプトを開発しました。

#### 結果

- **処理時間**: 2時間 → **10分未満**（約12倍高速化）
- **安定性**: エラーハンドリング実装で、処理が止まらない
- **操作性**: バックグラウンド実行可能、PCを他の作業に使える

---

## 🏗️ 実務で実装した設計思想

実務で完成させたスクリプトは、以下の設計思想で構築しました：

### 1. モジュール化設計

処理を分割し、それぞれ独立したモジュールとして実装。

```
project/
├── run.py                  # エントリーポイント
├── modules/
│   ├── extract.py         # ZIP展開・CSV読み込み
│   ├── transform.py       # フィルタリング・データ変換
│   ├── load.py            # Excel出力
│   └── cleanup.py         # 一時ファイル削除
└── tests/
    ├── test_extract.py
    ├── test_transform.py
    └── test_load.py
```

### 2. ルートスクリプト（run.py）での統合実行

各モジュールを `run.py` から呼び出し、ETLパイプライン全体を実行。

### 3. pytest によるテスト駆動開発

各モジュールごとにテストを作成し、機能の正確性を保証。

### 4. 段階的データフロー

```
入力 → 展開 → フィルタリング → 分割 → Excel化 → クリーンアップ
  ↓      ↓        ↓           ↓       ↓          ↓
 ZIP   temp/   filtered/    split/  output/   (削除)
```

各処理の出力を次の処理の入力とし、トレーサビリティを確保。

### 5. ストレージ管理

削除モジュールで不要な一時ファイルを自動削除し、ストレージの圧迫を防止。

### 6. Excel分割機能

Excelの仕様（最大1,048,576行）を考慮し、80万行を超えるデータは自動的に複数ファイルに分割。

### 7. Excel出力の最適化

- フォント調整
- カラム幅の自動調整
- ヘッダーの書式設定

---

## 🎯 今回のプロジェクト目的

### 実務で実装できなかった機能の追加

退職により未実装だった以下の機能を、今回のプロジェクトで実装します：

#### 1. GUIインターフェース

- フィルタリング条件をGUIで入力可能に
- パラメータ設定の柔軟性向上
- 初心者でも使いやすいUI

#### 2. デスクトップショートカット起動

- PowerShellでコマンドを打つ必要をなくす
- ダブルクリックで即起動
- Windows環境での運用性向上

### 開発の進め方

```
Phase 1: コアモジュール開発 + pytest
         ↓
Phase 2: ETL完成・統合テスト
         ↓
Phase 3: GUI実装
         ↓
Phase 4: ショートカット化
```

**重要**: GUI機能は、全てのモジュールが完成し、テストが通った後に追加する。

---

## 🚀 技術方針：Pandasベース開発

### Pandasを採用する理由

従来の標準ライブラリ（csv）ではなく、**pandas（DataFrame）を中心としたアーキテクチャ**で開発します。

#### メリット

| 項目         | 標準csv             | pandas                              |
| ------------ | ------------------- | ----------------------------------- |
| **処理速度** | 遅い（1行ずつ処理） | **高速（ベクトル演算）** ✅          |
| **メモリ**   | 少ない（5-10MB）    | 多い（500MB-1GB）                   |
| **可読性**   | 冗長なループ処理    | **宣言的で簡潔** ✅                  |
| **保守性**   | 低い                | **高い（DataFrameパイプライン）** ✅ |

#### 前提条件

- **メモリ16GB搭載PCを想定**
- 処理速度とコードの可読性を最優先
- ベクトル演算による高速化

#### DataFrame中心設計

**全モジュールの入出力を統一**:

```python
def module_name(
    input_files: List[Path],
    output_dir: Union[str, Path],
    verbose: bool = True
) -> List[Path]:
    """
    pandas + ファイル出力アプローチ
    
    内部でpandasのベクトル演算を使用し高速処理を実現。
    結果はCSVファイルとして保存され、パスのリストを返す。
    
    Args:
        input_files: 入力CSVファイルのリスト
        output_dir: 出力先ディレクトリ
        verbose: 詳細ログを出力するか
        
    Returns:
        List[Path]: 出力されたCSVファイルのPathリスト
        
    Examples:
        >>> output_files = module_name(csv_files, "output_dir", verbose=True)
    """
    output_files = []
    
    for input_path in input_files:
        # pandasでベクトル演算
        df = pd.read_csv(input_path, encoding='utf-8', keep_default_na=False)
        df['new_column'] = df['existing_column'].str.extract(pattern)
        
        # CSVとして保存
        output_path = output_dir / input_path.name
        df.to_csv(output_path, index=False, encoding='utf-8', na_rep='')
        output_files.append(output_path)
    
    return output_files
```

#### 主なベクトル演算パターン

```python
# 文字列抽出
df['protocol'] = df['Message'].str.extract(r'protocol=(\w+)')

# 文字列分割
df[['srcIP', 'dstIP']] = df['routing'].str.split(' > ', expand=True, n=1)

# フィルタリング
critical_df = df[df['Severity'] == 'CRITICAL']

# 条件判定
df['srcIP_type'] = df['srcIP'].apply(classify_ip_address)

# 列選択
reduced_df = df.iloc[:, [0, 1, 2, 6]]

# マージ
merged_df = pd.concat(df_list, ignore_index=True)
```

#### run.pyはオーケストレーター

```python
# イメージ（簡略版）
# 各モジュールは List[Path] → List[Path] + ファイル出力

# Phase 1: ZIP展開 + フィルタリング（ループ処理）
while zip_files:
    extracted_files = extract_zip(zip_file, temp_dir)
    filtered_files = filter_keyword(extracted_files, filtered_dir)
    cleanup_processed_files(zip_file, extracted_files)

# Phase 2: マージ
merged_files = merge_csv_files(filtered_files, merged_dir, max_rows=800000)

# Phase 3-10: 各種変換処理
reduced_files = reduce_columns(merged_files, reduced_dir, keep=[0,1,2,6])
routed_files = extract_routing(reduced_files, routed_dir)
splitted_files = split_ip(routed_files, splitted_dir)
classified_files = classify_ip(splitted_files, classified_dir)
protocol_files = extract_protocol(classified_files, protocol_dir)
severity_level_files = extract_severity_level(protocol_files, severity_level_dir)
severity_files = extract_severity(severity_level_files, severity_dir)
critical_file = filter_and_merge_critical(severity_files, "critical_merged.csv")

# 最終出力
export_to_excel(critical_file, output_path)
```

---

## 🏛️ システムアーキテクチャ

### ディレクトリ構成

```
juniper-syslog-filter/
├── source_logs/              # 手動でZIPファイルを配置（00.zip～23.zip）
├── temp_extracted/           # ZIP展開後の一時CSV（処理後削除）
├── filtered_logs/            # RT_IDP_ATTACK抽出後のCSV（処理後削除）
├── merged_logs/              # 80万行単位でマージ（処理後削除）
├── columns_reduced/          # 不要列削除後（処理後削除）
├── routing_added/            # routing列追加後（処理後削除）
├── ip_split/                 # srcIP/dstIP分離後（処理後削除）
├── ip_classified/            # IP判定（private/global）後（処理後削除）
├── protocol_extracted/       # protocol列抽出後（処理後削除）
├── severity_level_extracted/ # SeverityLevel列抽出後（処理後削除）
├── severity_extracted/       # Severity列抽出後（処理後削除）
├── critical_only/            # CRITICAL行のみ抽出後（処理後削除）
└── final_output/             # Excel最終出力先
```

### データフロー（全体像）

```
[手動配置]
  source_logs/
    ├── 00.zip
    ├── 01.zip
    ...
    └── 23.zip
         ↓
[run.py 実行開始]
         ↓
┌─────────────────────────────────────────┐
│ ループ処理（ZIPファイルが無くなるまで） │
│                                         │
│  1. ZIP展開                             │
│     source_logs/*.zip                   │
│     → temp_extracted/*.csv              │
│                                         │
│  2. キーワードフィルタ                  │
│     temp_extracted/*.csv                │
│     → filtered_logs/*.csv               │
│     （RT_IDP_ATTACKを含む行のみ）       │
│                                         │
│  3. クリーンアップ                      │
│     source_logs/処理済みZIP 削除        │
│     temp_extracted/*.csv 削除           │
│                                         │
└─────────────────────────────────────────┘
         ↓
[マージ処理]
  filtered_logs/*.csv
  → merged_logs/*.csv
  （80万行単位で分割）
         ↓
[列削除]
  SeverityLevel, Severity, LogType削除
  merged_logs/*.csv
  → columns_reduced/*.csv
  【状態】Timestamp, Hostname, AppName, Message
         ↓
[routing抽出]
  Message内から [srcip/port > dstip/port] 抽出
  columns_reduced/*.csv
  → routing_added/*.csv
  【状態】Timestamp, Hostname, AppName, routing, Message
         ↓
[IP分離]
  routingから srcIP, dstIP 分離（ポート番号削除）
  routing_added/*.csv
  → ip_split/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message
         ↓
[IP判定]
  srcIP, dstIPをprivate/global判定
  ip_split/*.csv
  → ip_classified/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, Message
         ↓
[protocol抽出]
  Message内から protocol=xxx 抽出
  ip_classified/*.csv
  → protocol_extracted/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, protocol, Message
         ↓
[SeverityLevel抽出]
  Message内から SeverityLevel=x 抽出
  protocol_extracted/*.csv
  → severity_level_extracted/*.csv
  【状態】..., protocol, SeverityLevel, Message
         ↓
[Severity抽出]
  Message内から Severity=xxx 抽出
  severity_level_extracted/*.csv
  → severity_extracted/*.csv
  【状態】..., SeverityLevel, Severity, Message
         ↓
[CRITICAL抽出]
  Severity=CRITICAL の行のみ抽出
  severity_extracted/*.csv
  → critical_only/*.csv
         ↓
[最終マージ（必要なら）]
  critical_only/*.csv（複数ファイルをマージ）
         ↓
[Excel出力]
  游ゴシック 11pt
  列幅自動調整
  → final_output/*.xlsx
```

### モジュール構成

| No  | モジュール                     | 責務                         | 入力                           | 出力                           |
| --- | ------------------------------ | ---------------------------- | ------------------------------ | ------------------------------ |
| 1   | `extract.py`                   | ZIP展開                      | source_logs/*.zip              | temp_extracted/*.csv           |
| 2   | `filter_keyword.py`            | キーワードフィルタ           | temp_extracted/*.csv           | filtered_logs/*.csv            |
| 3   | `cleanup_temp.py`              | 一時ファイル削除             | source_logs, temp_extracted    | -                              |
| 4   | `merge_files.py`               | 80万行単位でマージ           | filtered_logs/*.csv            | merged_logs/*.csv              |
| 5   | `reduce_columns.py`            | 不要列削除                   | merged_logs/*.csv              | columns_reduced/*.csv          |
| 6   | `extract_routing.py`           | routing列追加                | columns_reduced/*.csv          | routing_added/*.csv            |
| 7   | `split_ip.py`                  | srcIP/dstIP分離              | routing_added/*.csv            | ip_split/*.csv                 |
| 8   | `classify_ip.py`               | IP判定（private/global）     | ip_split/*.csv                 | ip_classified/*.csv            |
| 9   | `extract_protocol.py`          | protocol列追加               | ip_classified/*.csv            | protocol_extracted/*.csv       |
| 10  | `extract_severity_level.py`    | SeverityLevel列追加          | protocol_extracted/*.csv       | severity_level_extracted/*.csv |
| 11  | `extract_severity.py`          | Severity列追加               | severity_level_extracted/*.csv | severity_extracted/*.csv       |
| 12  | `filter_critical_and_merge.py` | CRITICAL行抽出 + マージ      | severity_extracted/*.csv       | critical_only/merged.csv       |
| 13  | `export_excel.py`              | Excel出力                    | critical_only/merged.csv       | final_output/*.xlsx            |
| -   | `cleanup_all.py`               | 全ディレクトリクリーンアップ | 各ディレクトリ                 | -                              |
| -   | `run.py`                       | パイプライン統合実行         | -                              | 処理結果                       |

---

## 📊 技術仕様

### 入力データ仕様

#### ログファイル構造

```
2025-04-28.zip               # 日次アーカイブ
├── 00.zip                   # 各時間のアーカイブ
│   └── 00.csv              # 時間別CSVログ
├── 01.zip
│   └── 01.csv
...
└── 23.zip
    └── 23.csv
```

#### CSVフォーマット

```csv
Timestamp,Hostname,AppName,SeverityLevel,Severity,LogType,Message
2025-12-16T00:46:22Z,srx-fw01,RT_SCREEN,2,CRITICAL,THREAT,RT_SCREEN_IP: IP spoofing detected 192.168.239.6/43657 > 80.86.112.63/8080 protocol=udp SeverityLevel=2 Severity=CRITICAL
```

| カラム        | データ型 | 説明                          |
| ------------- | -------- | ----------------------------- |
| Timestamp     | ISO8601  | ログ発生時刻                  |
| Hostname      | string   | ホスト名（例: srx-fw01）      |
| AppName       | string   | アプリ名（RT_FLOW, RT_IDP等） |
| SeverityLevel | int      | RFC5424準拠（0-7）            |
| Severity      | string   | 重要度（CRITICAL/WARNING等）  |
| LogType       | string   | THREAT / NORMAL               |
| Message       | string   | ログメッセージ本文            |

### 処理の詳細仕様

#### Phase 1: ループ処理（ファイルごと）

1. **ZIP展開**
   - `source_logs/` から1ファイルずつ処理
   - `temp_extracted/` に展開

2. **キーワードフィルタ**
   - `RT_IDP_ATTACK` を含む行のみ抽出
   - `filtered_logs/` に保存

3. **クリーンアップ**
   - 処理済みZIPを削除
   - 展開済みCSVを削除

#### Phase 2: 変換・抽出処理

4. **ファイルマージ**
   - 80万行を超える場合、複数ファイルに分割

5. **列削除**
   - `SeverityLevel`, `Severity`, `LogType` を削除
   - 残す列: `Timestamp`, `Hostname`, `AppName`, `Message`

6. **routing列抽出**
   - 正規表現: `(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+ > (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+`
   - 例: `192.168.1.1/12345 > 10.0.0.5/80` → `192.168.1.1 > 10.0.0.5`

7. **IP分離**
   - `routing` → `srcIP`, `dstIP`
   - 例: `192.168.1.1 > 10.0.0.5` → `srcIP=192.168.1.1`, `dstIP=10.0.0.5`

8. **IP判定**
   - プライベートIP範囲:
     - `10.0.0.0/8`
     - `172.16.0.0/12`
     - `192.168.0.0/16`
   - それ以外: `global`

9-11. **Message内データ抽出**
   - `protocol=xxx` → `protocol` 列
   - `SeverityLevel=x` → `SeverityLevel` 列
   - `Severity=xxx` → `Severity` 列

12. **CRITICAL抽出**
   - `Severity=CRITICAL` の行のみ

#### Phase 3: 最終出力

13. **最終マージ**
   - 複数ファイルを1つにまとめる

14. **Excel出力**
   - フォント: 游ゴシック 11pt
   - 列幅: 自動調整
   - ヘッダー: 太字

### 依存ライブラリ

```txt
pandas>=2.0.0
openpyxl>=3.1.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

---

## 💻 開発環境セットアップ

### 前提条件

- Windows 10/11
- Python 3.8以上
- Git
- VSCode（推奨）
- PowerShell

### 1. リポジトリのクローン

```powershell
git clone https://github.com/Sohey-k/juniper-syslog-filter.git
cd juniper-syslog-filter
```

### 2. uv のインストール

```powershell
# PowerShellで実行
irm https://astral.sh/uv/install.ps1 | iex
```

### 3. 仮想環境の作成

```powershell
# Python仮想環境作成（uvを使用）
uv venv

# 仮想環境の有効化
.\venv\Scripts\Activate.ps1
```

### 4. 依存パッケージのインストール

```powershell
# uvでパッケージインストール
uv pip install pandas openpyxl pytest
```

### 5. ディレクトリ構造の作成

```powershell
# 必要なディレクトリを作成
New-Item -ItemType Directory -Path source_logs -Force
```

### 6. VSCodeでプロジェクトを開く

```powershell
# VSCodeで現在のディレクトリを開く
code .
```

**VSCode推奨設定**（`.vscode/settings.json`）:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true
    },
    "files.encoding": "utf8"
}
```

**Flake8設定**（`.flake8`）:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
```

**Git改行コード設定**（`.gitattributes`）:

```
* text=auto eol=lf
```

これらの設定により：
- **settings.json**: VSCodeでのPython開発環境を最適化（インタープリタパス、フォーマッター設定）
- **.flake8**: コードスタイルチェックのルールを定義（Black互換の行長88文字）
- **.gitattributes**: Windows環境でのCRLF問題を防止（LF統一）

### 7. 開発の流れ

```powershell
# 毎回の作業開始時
cd juniper-syslog-filter
.\venv\Scripts\Activate.ps1

# パッケージ追加時
uv pip install <パッケージ名>
uv pip freeze > requirements.txt

# テスト実行
pytest

# 作業終了時
deactivate
```

### 8. requirements.txt（参考）

プロジェクト全体で使用するパッケージリスト：

```txt
pandas>=2.0.0
openpyxl>=3.1.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

インストール方法：
```powershell
uv pip install -r requirements.txt
```

---

## 📋 初期セットアップチェックリスト

プロジェクト開始前に確認：

- [ ] Python 3.8以上がインストール済み
- [ ] Git がインストール済み
- [ ] VSCode がインストール済み
- [ ] uv がインストール済み（`uv --version`で確認）
- [ ] venv仮想環境が作成済み
- [ ] 必要なパッケージがインストール済み（pandas, openpyxl, pytest）
- [ ] VSCodeでプロジェクトが開ける
- [ ] PowerShellでvenv有効化できる
- [ ] `source_logs/` ディレクトリが作成済み

---

## 📖 使用方法

### テストデータの生成

本プロジェクトには、Juniper SRX風のサンプルsyslogを生成するスクリプトが含まれています。

#### 基本的な使い方

```powershell
# デフォルト設定（2025-04-28、5000行/時、脅威率10%）
python scripts/generate_sample_data.py -o source_logs

# カスタム設定
python scripts/generate_sample_data.py \
  -o source_logs \
  -d 2025-12-18 \
  -r 10000 \
  -t 0.2
```

#### オプション

| オプション           | 説明                     | デフォルト    |
| -------------------- | ------------------------ | ------------- |
| `-o, --output`       | 出力ディレクトリ         | `output_logs` |
| `-d, --date`         | ログ日付 (YYYY-MM-DD)    | `2025-04-28`  |
| `-r, --rows`         | 1時間あたりの行数        | `5000`        |
| `-t, --threat-ratio` | 脅威ログの割合 (0.0-1.0) | `0.1`         |

#### 出力フォーマット

```csv
Timestamp,Hostname,AppName,SeverityLevel,Severity,LogType,Message
2025-04-28T00:15:32Z,srx-fw01,RT_IDP,2,CRITICAL,THREAT,RT_IDP_ATTACK_LOG: SQL injection attack detected 192.168.1.5/12345 > 203.0.113.10/80 protocol=tcp SeverityLevel=2 Severity=CRITICAL
```

### Phase 1-2: CLIモード

#### 前提条件

1. `source_logs/` ディレクトリに24個のZIPファイルを手動配置
   ```
   source_logs/
   ├── 00.zip
   ├── 01.zip
   ...
   └── 23.zip
   ```

2. Python環境の準備
   ```powershell
   pip install -r requirements.txt
   ```

#### 基本実行

```powershell
# シンプル実行（デフォルト設定）
python run.py

# 処理内容:
# 1. source_logs/ のZIPを1つずつ処理
# 2. RT_IDP_ATTACK を含む行を抽出
# 3. 列を再構成
# 4. Severity=CRITICAL の行のみ抽出
# 5. Excel形式で final_output/ に出力
```

#### 実行結果

```
final_output/
└── filtered_2025-04-28_CRITICAL.xlsx
```

### Phase 3: GUIモード

```powershell
python gui.py
```

- フィルタ条件をGUI上で選択
- キーワード変更可能（デフォルト: RT_IDP_ATTACK）
- Severity選択可能（デフォルト: CRITICAL）
- 「実行」ボタンで処理開始

### Phase 4: ショートカット起動

デスクトップアイコンをダブルクリック → GUIが起動

---

## 🧪 テスト戦略

### 単体テスト（pytest）

各モジュールごとに作成：

```python
# test_extract.py
def test_extract_zip():
    """ZIP展開が正常に動作するか"""
    pass

def test_read_csv():
    """CSV読み込みが正常に動作するか"""
    pass
```

### pandasテスト

DataFrameの検証には `pd.testing.assert_frame_equal` を使用：

```python
import pandas as pd
import pandas.testing as pdt

def test_dataframe_processing():
    """DataFrameの処理が正しいか検証"""
    expected = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    result = process_dataframe(input_df)
    
    pdt.assert_frame_equal(result, expected)
```

### 統合テスト

エンドツーエンドでの動作確認：

```python
# test_integration.py
def test_full_pipeline():
    """入力→出力まで全パイプラインをテスト"""
    pass
```

### テストデータ

- サンプルZIPファイル（小規模: 1,000行）
- サンプルZIPファイル（大規模: 1,000,000行）

---

## 📁 プロジェクト構成

```
juniper-syslog-filter/
├── README.md                          # プロジェクト概要
├── DESIGN_DOCUMENT.md                 # 本ドキュメント
├── requirements.txt                   # 依存ライブラリ
├── setup.py                           # パッケージ設定
├── run.py                             # エントリーポイント（CLI）
├── gui.py                             # GUI起動スクリプト（Phase 3）
│
├── # 開発環境設定
├── .flake8                            # Flake8コードチェッカー設定
├── .gitattributes                     # Git改行コード設定（CRLF対策）
├── .vscode/
│   └── settings.json                  # VSCode設定（フォーマッター等）
│
├── scripts/                           # 開発ツール・補助スクリプト
│   └── generate_sample_data.py       # サンプルsyslog生成スクリプト
│
├── modules/                           # コアモジュール
│   ├── __init__.py
│   │
│   ├── # ループ処理モジュール
│   ├── extract.py                    # ZIP展開
│   ├── filter_keyword.py             # キーワードフィルタ
│   ├── cleanup_temp.py               # 一時ファイル削除
│   │
│   ├── # 変換・抽出モジュール
│   ├── merge_files.py                # 80万行マージ
│   ├── reduce_columns.py             # 列削除
│   ├── extract_routing.py            # routing抽出
│   ├── split_ip.py                   # IP分離
│   ├── classify_ip.py                # IP判定
│   ├── extract_protocol.py           # protocol抽出
│   ├── extract_severity_level.py     # SeverityLevel抽出
│   ├── extract_severity.py           # Severity抽出
│   ├── filter_critical_and_merge.py  # CRITICAL抽出 + マージ
│   │
│   ├── # 最終出力モジュール
│   ├── export_excel.py               # Excel出力
│   └── cleanup_all.py                # 全ディレクトリクリーンアップ
│
├── tests/                             # テストコード
│   ├── __init__.py
│   ├── test_extract.py
│   ├── test_filter_keyword.py
│   ├── test_cleanup_temp.py
│   ├── test_merge_files.py
│   ├── test_reduce_columns.py
│   ├── test_extract_routing.py
│   ├── test_split_ip.py
│   ├── test_classify_ip.py
│   ├── test_extract_protocol.py
│   ├── test_extract_severity_level.py
│   ├── test_extract_severity.py
│   ├── test_filter_critical_and_merge.py
│   ├── test_export_excel.py
│   ├── test_cleanup_all.py
│   └── test_integration.py
│
├── # データディレクトリ（実行時に自動生成）
├── source_logs/                       # 入力ZIPファイル配置（手動）
├── temp_extracted/                    # ZIP展開後（一時）
├── filtered_logs/                     # キーワードフィルタ後（一時）
├── merged_logs/                       # マージ後（一時）
├── columns_reduced/                   # 列削除後（一時）
├── routing_added/                     # routing追加後（一時）
├── ip_split/                          # IP分離後（一時）
├── ip_classified/                     # IP判定後（一時）
├── protocol_extracted/                # protocol抽出後（一時）
├── severity_level_extracted/          # SeverityLevel抽出後（一時）
├── severity_extracted/                # Severity抽出後（一時）
├── critical_only/                     # CRITICAL抽出後（一時）
├── final_output/                      # Excel最終出力
│
└── docs/                              # 追加ドキュメント
    ├── architecture.md
    └── api_reference.md
```

---

## 🎓 学んだこと・実務での成果

### 技術的な学び

- **Python ETL開発**: 実務未経験から本番運用レベルまで到達
- **モジュール設計**: 保守性・拡張性の高い設計手法
- **テスト駆動開発**: pytestによる品質保証
- **パフォーマンス最適化**: 2時間→10分の劇的な改善
- **pandas活用**: ベクトル演算による高速処理

### ソフトスキル

- **問題発見力**: 「当たり前」に疑問を持つ
- **GPT/Claude活用**: 学習パートナーとしての活用
- **ユーザー視点**: オペレーターの作業負担を考慮した設計

### 開発アプローチ

本プロジェクトの設計および実装においては、生成AI（ChatGPT/Claude）を補助的な壁打ち・設計整理ツールとして活用しています。ただし、**処理方針の決定、検証、実装、テストはすべて開発者自身が行っており**、AIはあくまで思考の整理やコード品質向上のサポート役として位置づけています。

---

## 🔮 今後の展望

### 追加機能案

- [ ] Slackへの通知機能
- [ ] スケジュール実行（cronライク）
- [ ] ログレベルでの統計情報出力
- [ ] ダッシュボード機能（Streamlit等）

### コミュニティ貢献

- GitHub公開でオープンソース化
- 他のsyslog形式への対応
- Docker化

---

## 📝 ライセンス

MIT License

---

## 👤 作者

**Sohey-k**

- GitHub: https://github.com/Sohey-k
- 実務経験を基にした、実践的なETLツール開発

---

## 📅 更新履歴

| 日付       | バージョン | 内容                                                                       |
| ---------- | ---------- | -------------------------------------------------------------------------- |
| 2025-12-16 | 1.0.0      | 初版作成・設計書完成                                                       |
| 2025-12-16 | 1.1.0      | 詳細な処理フロー反映・14モジュール構成に更新                               |
| 2025-12-16 | 1.2.0      | 開発環境セットアップ追加（uv + venv + VSCode + PowerShell）                |
| 2025-12-18 | 2.0.0      | pandas方針追加・scripts/ディレクトリ追加・サンプルデータ生成スクリプト統合 |
| 2025-12-18 | 2.1.0      | pandas実装完了・インターフェース設計を実際の実装に更新（List[Path]方式）   |
| 2025-12-19 | 2.2.0      | Phase 10統合反映・開発環境設定ファイル追加・AI利用方針明記                 |

---