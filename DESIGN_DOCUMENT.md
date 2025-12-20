# Juniper Syslog フィルタリングツール - 設計書 v3.0

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

- **処理時間**: 2時間 → **3分**（約40倍高速化）✨
- **安定性**: エラーハンドリング実装で、処理が止まらない
- **操作性**: バックグラウンド実行可能、PCを他の作業に使える

#### 実測パフォーマンス

| データ量         | 入力行数  | フィルタ後 | CLI処理時間  | Web処理時間 |
| ---------------- | --------- | ---------- | ------------ | ----------- |
| **実務データ**   | 3,360万行 | 約2-20万行 | **3分1秒** ⚡ | 約12分      |
| **テストデータ** | 480万行   | 約120万行  | 6分32秒      | 約13分      |

**重要**: 処理時間はフィルタ後のデータ量に依存します。脅威検知が多い日は処理時間が増加する可能性があります。

---

## 🏗️ 実務で実装した設計思想

実務で完成させたスクリプトは、以下の設計思想で構築しました：

### 1. モジュール化設計

処理を分割し、それぞれ独立したモジュールとして実装。

```
project/
├── run.py                  # エントリーポイント
├── run_with_args.py        # 引数対応CLI（Web版の内部処理用）
├── run_gui.py              # Web UI（Streamlit）
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
**経過時間表示機能**により、各Phase完了時と合計実行時間を表示。

### 3. pytest によるテスト駆動開発

各モジュールごとにテストを作成し、機能の正確性を保証。  
**59個のテストケース**で全機能をカバー。

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

- **xlsxwriter導入**: openpyxlの2-3倍の速度で出力
- フォント調整
- カラム幅の自動調整
- ヘッダーの書式設定

---

## 🎯 今回のプロジェクト目的

### 実務で実装できなかった機能の追加

退職により未実装だった以下の機能を、今回のプロジェクトで実装します：

#### 1. GUIインターフェース（✅ 完成）

- フィルタリング条件をGUIで入力可能
- パラメータ設定の柔軟性向上
- **リアルタイム進捗表示**（Phase別）
- **経過時間表示**（処理中・完了時）
- 初心者でも使いやすいUI

#### 2. デスクトップショートカット起動（✅ 完成）

- PowerShellでコマンドを打つ必要をなくす
- ダブルクリックで即起動
- Windows環境での運用性向上

### 開発の進め方

```
Phase 1: コアモジュール開発 + pytest ✅
         ↓
Phase 2: ETL完成・統合テスト ✅
         ↓
Phase 3: GUI実装 ✅
         ↓
Phase 4: ショートカット化 ✅
         ↓
Phase 5: 実務データ負荷テスト ✅
```

**すべてのPhaseが完了しました** 🎉

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

- **メモリ16GB以上搭載PCを想定**（32GB推奨）
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

import time

# 処理開始時刻を記録
start_time = time.time()

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

# Phase 10: CRITICAL抽出（マージなし、複数ファイル出力）
critical_files = filter_critical(severity_files, critical_dir)

# Phase 11: Excel最終出力（複数ファイルをループ処理）
for critical_file in critical_files:
    export_to_excel(critical_file, final_output_dir)

# 合計実行時間を表示
total_time = format_elapsed_time(start_time)
print(f"🎉 全処理完了！ ⏱️  合計実行時間: {total_time}")
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
├── reduced_logs/             # 不要列削除後（処理後削除）
├── routed_logs/              # routing列追加後（処理後削除）
├── splitted_logs/            # srcIP/dstIP分離後（処理後削除）
├── classified_logs/          # IP判定（private/global）後（処理後削除）
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
  → reduced_logs/*.csv
  【状態】Timestamp, Hostname, AppName, Message
         ↓
[routing抽出]
  Message内から [srcip/port > dstip/port] 抽出
  reduced_logs/*.csv
  → routed_logs/*.csv
  【状態】Timestamp, Hostname, AppName, routing, Message
         ↓
[IP分離]
  routingから srcIP, dstIP 分離（ポート番号削除）
  routed_logs/*.csv
  → splitted_logs/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message
         ↓
[IP判定]
  srcIP, dstIPをprivate/global判定
  splitted_logs/*.csv
  → classified_logs/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, Message
         ↓
[protocol抽出]
  Message内から protocol=xxx 抽出
  classified_logs/*.csv
  → protocol_extracted/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, srcIP_type, dstIP, dstIP_type, protocol, Message
         ↓
[SeverityLevel抽出]
  Message内から SeverityLevel=数字 抽出
  protocol_extracted/*.csv
  → severity_level_extracted/*.csv
  【状態】上記 + SeverityLevel
         ↓
[Severity抽出]
  Message内から Severity=xxx 抽出
  severity_level_extracted/*.csv
  → severity_extracted/*.csv
  【状態】上記 + Severity
         ↓
[CRITICAL抽出]（Phase 10）
  Severity == 'CRITICAL' の行のみ抽出
  severity_extracted/*.csv
  → critical_only/*.csv（複数ファイル、マージなし）
         ↓
[Excel出力]（Phase 11）
  critical_only/*.csv（複数ファイル）
  → final_output/*.xlsx（複数ファイル、ループ処理）
  
  ※ xlsxwriterによる高速出力（openpyxlの2-3倍）
         ↓
[全クリーンアップ]（Phase 12）
  中間ディレクトリを全削除
         ↓
[処理完了]
  🎉 全処理完了！ ⏱️  合計実行時間: 3分1秒
```

---

## 📦 モジュール仕様

### 全12フェーズの処理モジュール

#### Phase 1: ループ処理モジュール

**1. extract.py** - ZIP展開
```python
def extract_zip(zip_path: Path, output_dir: Path) -> List[Path]
```
- ZIPファイルを展開し、CSVファイルのリストを返す

**2. filter_keyword.py** - キーワードフィルタ
```python
def filter_keyword(
    input_files: List[Path],
    output_dir: Path,
    keyword: str = "RT_IDP_ATTACK",
    verbose: bool = True
) -> int
```
- 指定キーワードを含む行のみ抽出
- フィルタされた行数を返す

**3. cleanup_temp.py** - 一時ファイル削除
```python
def cleanup_processed_files(
    zip_file: Path,
    csv_files: List[Path],
    verbose: bool = True
) -> None
```
- 処理済みZIPと一時CSVを削除

#### Phase 2: マージモジュール

**4. merge_files.py** - 80万行マージ
```python
def merge_csv_files(
    input_files: List[Path],
    output_dir: Path,
    max_rows: int = 800000,
    verbose: bool = True
) -> List[Path]
```
- 80万行を超えないように自動分割してマージ

#### Phase 3-9: 変換・抽出モジュール

**5. reduce_columns.py** - 列削除
```python
def reduce_columns(
    input_files: List[Path],
    output_dir: Path,
    keep_columns: List[int] = [0, 1, 2, 6],
    verbose: bool = True
) -> List[Path]
```
- 指定列のみ保持

**6. extract_routing.py** - routing抽出
```python
def extract_routing(
    input_files: List[Path],
    output_dir: Path,
    verbose: bool = True
) -> List[Path]
```
- Message列から routing情報を抽出

**7. split_ip.py** - IP分離
```python
def split_ip(
    input_files: List[Path],
    output_dir: Path,
    verbose: bool = True
) -> List[Path]
```
- routing列から srcIP, dstIP を分離

**8. classify_ip.py** - IP判定
```python
def classify_ip(
    input_files: List[Path],
    output_dir: Path,
    verbose: bool = True
) -> List[Path]
```
- IPアドレスをprivate/global判定

**9. extract_protocol.py** - protocol抽出
```python
def extract_protocol(
    input_files: List[Path],
    output_dir: Path,
    verbose: bool = True
) -> List[Path]
```
- Message列から protocol情報を抽出

**10. extract_severity_level.py** - SeverityLevel抽出
```python
def extract_severity_level(
    input_files: List[Path],
    output_dir: Path,
    verbose: bool = True
) -> List[Path]
```
- Message列から SeverityLevel を抽出

**11. extract_severity.py** - Severity抽出
```python
def extract_severity(
    input_files: List[Path],
    output_dir: Path,
    verbose: bool = True
) -> List[Path]
```
- Message列から Severity を抽出

#### Phase 10: CRITICAL抽出モジュール

**12. filter_critical.py** - CRITICAL抽出（マージなし）
```python
def filter_critical(
    input_files: List[Path],
    output_dir: Union[str, Path],
    severity_filter: str = "CRITICAL",
    verbose: bool = True
) -> List[Path]
```
- Severity == 'CRITICAL' の行のみ抽出
- **マージ処理なし**（複数ファイルのまま出力）
- Excel行数制限（104万行）回避のため

#### Phase 11: Excel出力モジュール

**13. export_excel.py** - Excel出力（xlsxwriter版）
```python
def export_to_excel(
    input_csv: Path,
    output_dir: Union[str, Path],
    font_name: str = "Meiryo UI",
    font_size: int = 10,
    verbose: bool = True
) -> Path
```
- **xlsxwriter使用**（openpyxlの2-3倍高速）
- フォント設定、列幅自動調整
- Phase 11では複数ファイルをループ処理

#### Phase 12: クリーンアップモジュール

**14. cleanup_all.py** - 全ディレクトリクリーンアップ
```python
def cleanup_all_directories(
    project_root: Path,
    verbose: bool = True
) -> int
```
- 中間ディレクトリを全削除
- final_output/ のみ残す

---

## 🖥️ 実行方法

### 開発環境セットアップ

#### 1. Python環境準備

```powershell
# Pythonバージョン確認（3.8以上）
python --version

# uvのインストール確認
uv --version
```

#### 2. プロジェクトのクローン

```powershell
git clone https://github.com/Sohey-k/juniper-syslog-generator.git
cd juniper-syslog-generator
```

#### 3. 仮想環境の作成と有効化

```powershell
# venv作成
uv venv

# 有効化（PowerShell）
venv\Scripts\activate

# 有効化（コマンドプロンプト）
venv\Scripts\activate.bat
```

#### 4. 依存パッケージのインストール

```powershell
# requirements.txtからインストール
uv pip install -r requirements.txt

# または個別インストール
uv pip install pandas openpyxl xlsxwriter pytest streamlit
```

#### 5. VSCode設定（オプション）

```powershell
# .vscode/settings.json が自動適用される
# - Pythonインタープリタ: ./venv/Scripts/python.exe
# - フォーマッター: black
# - リンター: flake8
```

#### 6. テスト実行

```powershell
# 全テスト実行（59テスト）
pytest

# カバレッジ付き
pytest --cov=modules --cov-report=html

# 作業終了時
deactivate
```

### requirements.txt

プロジェクト全体で使用するパッケージリスト：

```txt
pandas>=2.0.0
openpyxl>=3.1.0
xlsxwriter>=3.0.0
streamlit>=1.28.0
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
- [ ] 必要なパッケージがインストール済み（pandas, openpyxl, xlsxwriter, pytest, streamlit）
- [ ] VSCodeでプロジェクトが開ける
- [ ] PowerShellでvenv有効化できる
- [ ] `source_logs/` ディレクトリが作成済み

---

## 📖 使用方法

### テストデータの生成

本プロジェクトには、Juniper SRX風のサンプルsyslogを生成するスクリプトが含まれています。

#### 基本的な使い方

```powershell
# 実務データ再現（推奨）
python generator.py -o source_logs -d 2025-12-20 -H mx240 -r 1400000 -t 0.005

# テストデータ（軽量）
python generator.py -o source_logs -r 200000 -t 0.5
```

#### オプション

| オプション           | 説明                     | デフォルト    |
| -------------------- | ------------------------ | ------------- |
| `-o, --output`       | 出力ディレクトリ         | `output_logs` |
| `-d, --date`         | ログ日付 (YYYY-MM-DD)    | `2025-04-28`  |
| `-H, --hostname`     | ホスト名                 | `srx-fw01`    |
| `-r, --rows`         | 1時間あたりの行数        | `5000`        |
| `-t, --threat-ratio` | 脅威ログの割合 (0.0-1.0) | `0.1`         |

#### 実務データ再現の例

```powershell
# 1日分 3,360万行、脅威出現率0.5%（実務相当）
python generator.py -o source_logs -r 1400000 -t 0.005

# 生成結果:
# - source_logs/2025-04-28.zip（約1GB）
# - 24時間分のZIPファイルを含む
```

#### 出力フォーマット

```csv
Timestamp,Hostname,AppName,SeverityLevel,Severity,LogType,Message
2025-04-28T00:15:32Z,srx-fw01,RT_IDP,2,CRITICAL,THREAT,RT_IDP_ATTACK_LOG: SQL injection attack detected 192.168.1.5/12345 > 203.0.113.10/80 protocol=tcp SeverityLevel=2 Severity=CRITICAL
```

### CLI実行方法

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

#### 基本実行（標準版）

```powershell
# デフォルト実行
python run.py

# 処理内容:
# 1. source_logs/ のZIPを1つずつ処理
# 2. RT_IDP_ATTACK を含む行を抽出
# 3. 列を再構成
# 4. Severity=CRITICAL の行のみ抽出
# 5. Excel形式で final_output/ に複数ファイルとして出力
```

#### 引数付き実行（パラメータ変更）

```powershell
# run_with_args.py を使用
python run_with_args.py --keyword RT_SCREEN --severity WARNING

# オプション:
#   --keyword: フィルタキーワード（デフォルト: RT_IDP_ATTACK）
#   --severity: Severityフィルタ（CRITICAL/WARNING/INFO）
```

#### 実行ログ例

```
======================================================================
Juniper Syslog Filter - Starting...
======================================================================

[Phase 1] Loop processing started
----------------------------------------------------------------------
[ZIP] Processing: 00.zip
  |- Extracting... OK (1 files)
  |- Filtering... OK (60198 rows)
  +- Cleanup... OK
...
======================================================================
✅ Phase 1 完了 ⏱️  経過時間: 0分34秒
======================================================================

[Phase 2] Merge processing started
...
======================================================================
✅ Phase 2 完了 ⏱️  経過時間: 0分45秒
======================================================================

...

======================================================================
✅ Phase 12 完了 ⏱️  経過時間: 2分58秒
======================================================================

🎉 全処理完了！ ⏱️  合計実行時間: 3分1秒
======================================================================
```

#### 実行結果

```
final_output/
├── merged_001.xlsx
└── merged_002.xlsx
```

### Web GUI実行方法

#### 起動方法

```powershell
# Streamlit起動
streamlit run run_gui.py

# または、バッチファイルから
start_gui.bat
```

#### 機能

- ✅ **リアルタイム進捗表示**（Phase別）
- ✅ **経過時間表示**（処理中・完了時）
- ✅ **パラメータ変更**（キーワード・Severity）
- ✅ **出力ファイル一覧表示**
- ✅ **実行ログ確認**

#### 画面イメージ

```
🔥 Juniper Syslog Filter
────────────────────────────────────

⚙️ 設定                    │ 📊 処理ステータス
                           │ 🔄 Phase 5 完了... ⏱️ 経過時間: 6分23秒
フィルタキーワード          │
[RT_IDP_ATTACK    ]        │ 📝 処理ログ
                           │ [ZIP] Processing: 12.zip
Severityフィルタ           │   |- Extracting... OK
[CRITICAL        ▼]        │   |- Filtering... OK
                           │ [Phase 5] IP split started
─────────────────          │ [Files] Target: 2
💡 リアルタイム進捗表示     │ [Split] Processing... OK
                           │
[🚀 実行              ]    │
```

#### 処理速度について

| バージョン | 処理時間    | 特徴                          |
| ---------- | ----------- | ----------------------------- |
| **CLI版**  | **3-7分** ⚡ | 最速、経過時間表示あり        |
| **Web版**  | **12-15分** | GUI操作可能、リアルタイム進捗 |

**注意**: Web版はsubprocess経由のため、CLI版より時間がかかります。速さを求める場合はCLI版をお勧めします。

### デスクトップショートカット起動

#### start_gui.bat の内容

```batch
@echo off
REM Juniper Syslog Filter - GUI起動スクリプト

echo ========================================
echo  Juniper Syslog Filter - GUI起動中...
echo ========================================
echo.

REM プロジェクトディレクトリに移動
cd /d "%~dp0"

REM 仮想環境を有効化
call venv\Scripts\activate.bat

REM Streamlit GUIを起動
echo [INFO] ブラウザが自動で開きます...
echo [INFO] 終了するにはこのウィンドウを閉じてください
echo.

streamlit run run_gui.py

REM 終了時の処理
echo.
echo ========================================
echo  処理が終了しました
echo ========================================
pause
```

#### ショートカット作成

```powershell
# デスクトップにショートカット作成
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\Juniper Syslog Filter.lnk")
$Shortcut.TargetPath = "$PWD\start_gui.bat"
$Shortcut.WorkingDirectory = "$PWD"
$Shortcut.IconLocation = "C:\Windows\System32\cmd.exe, 0"
$Shortcut.Save()
```

---

## 🧪 テスト戦略

### テストカバレッジ

**59個のテストケース**で全機能をカバー：

```powershell
# 全テスト実行
pytest

# 結果例:
============================= test session starts ==============================
collected 59 items

tests/test_extract.py ............                                       [ 20%]
tests/test_filter_keyword.py ....                                        [ 27%]
tests/test_cleanup_temp.py ....                                          [ 33%]
tests/test_merge_files.py .....                                          [ 42%]
tests/test_reduce_columns.py ....                                        [ 49%]
tests/test_extract_routing.py ....                                       [ 56%]
tests/test_split_ip.py .....                                             [ 65%]
tests/test_classify_ip.py .....                                          [ 74%]
tests/test_extract_protocol.py ....                                      [ 81%]
tests/test_extract_severity_level.py ....                                [ 88%]
tests/test_extract_severity.py ....                                      [ 93%]
tests/test_filter_critical.py ....                                       [ 97%]
tests/test_export_excel.py ....                                          [100%]

============================== 59 passed in 6.60s ===============================
```

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
- 実務データ再現（3,360万行、脅威0.5%）

---

## 📁 プロジェクト構成

```
juniper-syslog-filter/
├── README.md                          # プロジェクト概要
├── DESIGN_DOCUMENT.md                 # 本ドキュメント
├── requirements.txt                   # 依存ライブラリ
├── generator.py                       # サンプルsyslog生成スクリプト
├── run.py                             # エントリーポイント（CLI）
├── run_with_args.py                   # 引数対応CLI（Web版内部処理用）
├── run_gui.py                         # Web UI（Streamlit）
├── start_gui.bat                      # GUI起動バッチファイル
│
├── # 開発環境設定
├── .gitattributes                     # Git改行コード設定（CRLF対策）
├── .vscode/
│   └── settings.json                  # VSCode設定（フォーマッター等）
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
│   ├── filter_critical.py            # CRITICAL抽出（マージなし）
│   │
│   ├── # 最終出力モジュール
│   ├── export_excel.py               # Excel出力（xlsxwriter版）
│   └── cleanup_all.py                # 全ディレクトリクリーンアップ
│
├── tests/                             # テストコード（59テスト）
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
│   ├── test_filter_critical.py       # Phase 10テスト
│   ├── test_export_excel.py
│   └── test_cleanup_all.py
│
├── # データディレクトリ（実行時に自動生成）
├── source_logs/                       # 入力ZIPファイル配置（手動）
├── temp_extracted/                    # ZIP展開後（一時）
├── filtered_logs/                     # キーワードフィルタ後（一時）
├── merged_logs/                       # マージ後（一時）
├── reduced_logs/                      # 列削除後（一時）
├── routed_logs/                       # routing追加後（一時）
├── splitted_logs/                     # IP分離後（一時）
├── classified_logs/                   # IP判定後（一時）
├── protocol_extracted/                # protocol抽出後（一時）
├── severity_level_extracted/          # SeverityLevel抽出後（一時）
├── severity_extracted/                # Severity抽出後（一時）
├── critical_only/                     # CRITICAL抽出後（一時）
└── final_output/                      # Excel最終出力
```

---

## 🎓 学んだこと・実務での成果

### 技術的な学び

- **Python ETL開発**: 実務未経験から本番運用レベルまで到達
- **モジュール設計**: 保守性・拡張性の高い設計手法
- **テスト駆動開発**: pytestによる品質保証（59テスト）
- **パフォーマンス最適化**: 2時間→3分の劇的な改善（約40倍高速化）
- **pandas活用**: ベクトル演算による高速処理
- **xlsxwriter活用**: Excel出力の2-3倍高速化

### ソフトスキル

- **問題発見力**: 「当たり前」に疑問を持つ
- **GPT/Claude活用**: 学習パートナーとしての活用
- **ユーザー視点**: オペレーターの作業負担を考慮した設計

### 開発アプローチ

本プロジェクトの設計および実装においては、生成AI（ChatGPT/Claude）を補助的な壁打ち・設計整理ツールとして活用しています。ただし、**処理方針の決定、検証、実装、テストはすべて開発者自身が行っており**、AIはあくまで思考の整理やコード品質向上のサポート役として位置づけています。

---

## 🔮 今後の展望

### 追加機能案

- [x] Slackへの通知機能（実装候補）
- [ ] スケジュール実行（cronライク）
- [ ] ログレベルでの統計情報出力
- [ ] ダッシュボード機能（Streamlit拡張）

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

| 日付       | バージョン | 内容                                                                                         |
| ---------- | ---------- | -------------------------------------------------------------------------------------------- |
| 2025-12-16 | 1.0.0      | 初版作成・設計書完成                                                                         |
| 2025-12-16 | 1.1.0      | 詳細な処理フロー反映・14モジュール構成に更新                                                 |
| 2025-12-16 | 1.2.0      | 開発環境セットアップ追加（uv + venv + VSCode + PowerShell）                                  |
| 2025-12-18 | 2.0.0      | pandas方針追加・scripts/ディレクトリ追加・サンプルデータ生成スクリプト統合                   |
| 2025-12-18 | 2.1.0      | pandas実装完了・インターフェース設計を実際の実装に更新（List[Path]方式）                     |
| 2025-12-19 | 2.2.0      | Phase 10統合反映・開発環境設定ファイル追加・AI利用方針明記                                   |
| 2025-12-20 | 3.0.0      | **Phase 10-12完全実装・xlsxwriter導入・Web GUI完成・経過時間表示・実務データ負荷テスト完了** |

### v3.0.0の主な変更点

#### 機能追加
- ✅ **Phase 10**: filter_critical.py（マージ削除、複数ファイル出力）
- ✅ **Phase 11**: 複数ファイルのループ処理対応
- ✅ **xlsxwriter導入**: Excel出力を2-3倍高速化
- ✅ **経過時間表示**: CLI版でPhase別・合計時間表示
- ✅ **Web GUI完成**: Streamlit実装、リアルタイム進捗表示
- ✅ **run_with_args.py**: 引数対応CLI（Web版内部処理用）

#### パフォーマンス
- ✅ **実務データ処理**: 3,360万行を3分1秒で処理（実測）
- ✅ **Excel出力**: openpyxl → xlsxwriter（2-3倍高速化）

#### テスト
- ✅ **59テストケース**: 全モジュールをカバー
- ✅ **実務データ負荷テスト**: 完了

#### ドキュメント
- ✅ **処理時間実測値**: 反映
- ✅ **ファイル構成**: 最新版に更新
- ✅ **使用方法**: CLI/Web両対応

---