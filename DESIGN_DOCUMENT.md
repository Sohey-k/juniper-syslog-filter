# Juniper Syslog フィルタリングツール - 設計書

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
使用されていたツールは **SikuliX** で作成されたスクリプトでしたが、以下の深刻な問題を抱えていました：

#### SikuliXスクリプトの問題点

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

## 🏛️ システムアーキテクチャ

### ディレクトリ構成

```
project/
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
│     （[RT_IDP_ATTACK]を含む行のみ）     │
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
  【状態】Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, Message
         ↓
[protocol抽出]
  Message内から protocol=xxx 抽出
  ip_classified/*.csv
  → protocol_extracted/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, protocol, Message
         ↓
[SeverityLevel抽出]
  Message内から SeverityLevel=x 抽出
  protocol_extracted/*.csv
  → severity_level_extracted/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, protocol, SeverityLevel, Message
         ↓
[Severity抽出]
  Message内から Severity=xxx 抽出
  severity_level_extracted/*.csv
  → severity_extracted/*.csv
  【状態】Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, protocol, SeverityLevel, Severity, Message
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

| No  | モジュール                  | 責務                         | 入力                           | 出力                           |
| --- | --------------------------- | ---------------------------- | ------------------------------ | ------------------------------ |
| 1   | `extract.py`                | ZIP展開                      | source_logs/*.zip              | temp_extracted/*.csv           |
| 2   | `filter_keyword.py`         | キーワードフィルタ           | temp_extracted/*.csv           | filtered_logs/*.csv            |
| 3   | `cleanup_temp.py`           | 一時ファイル削除             | source_logs, temp_extracted    | -                              |
| 4   | `merge_files.py`            | 80万行単位でマージ           | filtered_logs/*.csv            | merged_logs/*.csv              |
| 5   | `reduce_columns.py`         | 不要列削除                   | merged_logs/*.csv              | columns_reduced/*.csv          |
| 6   | `extract_routing.py`        | routing列追加                | columns_reduced/*.csv          | routing_added/*.csv            |
| 7   | `split_ip.py`               | srcIP/dstIP分離              | routing_added/*.csv            | ip_split/*.csv                 |
| 8   | `classify_ip.py`            | IP判定（private/global）     | ip_split/*.csv                 | ip_classified/*.csv            |
| 9   | `extract_protocol.py`       | protocol列追加               | ip_classified/*.csv            | protocol_extracted/*.csv       |
| 10  | `extract_severity_level.py` | SeverityLevel列追加          | protocol_extracted/*.csv       | severity_level_extracted/*.csv |
| 11  | `extract_severity.py`       | Severity列追加               | severity_level_extracted/*.csv | severity_extracted/*.csv       |
| 12  | `filter_critical.py`        | CRITICAL行のみ抽出           | severity_extracted/*.csv       | critical_only/*.csv            |
| 13  | `final_merge.py`            | 最終マージ                   | critical_only/*.csv            | critical_only/merged.csv       |
| 14  | `export_excel.py`           | Excel出力                    | critical_only/*.csv            | final_output/*.xlsx            |
| -   | `cleanup_all.py`            | 全ディレクトリクリーンアップ | 各ディレクトリ                 | -                              |
| -   | `run.py`                    | パイプライン統合実行         | -                              | 処理結果                       |

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
   - Message列に `RT_IDP_ATTACK` を含む行のみ抽出
   - `filtered_logs/` に保存

3. **クリーンアップ**
   - 処理済みZIPを `source_logs/` から削除
   - `temp_extracted/` のCSVを削除

#### Phase 2: マージ・列操作処理

4. **80万行マージ**
   - `filtered_logs/` の全CSVを統合
   - 80万行を超えたら別ファイルに分割
   - `merged_logs/` に保存

5. **不要列削除**
   - `SeverityLevel`, `Severity`, `LogType` 列を削除
   - 残る列: `Timestamp, Hostname, AppName, Message`
   - `columns_reduced/` に保存

6. **routing抽出**
   - Message内の `[srcip/port > dstip/port]` を抽出
   - 新規列 `routing` を `AppName` と `Message` の間に挿入
   - 列: `Timestamp, Hostname, AppName, routing, Message`
   - `routing_added/` に保存

7. **IP分離**
   - `routing` 列から srcIP, dstIP を分離
   - ポート番号（`/` 以降）を削除
   - 列: `Timestamp, Hostname, AppName, routing, srcIP, dstIP, Message`
   - `ip_split/` に保存

8. **IP判定**
   - srcIP, dstIP それぞれをprivate/global判定
   - 判定結果を `judge` 列として各IPの右に追加
   - 列: `Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, Message`
   - `ip_classified/` に保存

9. **protocol抽出**
   - Message内の `protocol=xxx` を抽出
   - 新規列 `protocol` を `judge` と `Message` の間に挿入
   - 列: `Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, protocol, Message`
   - `protocol_extracted/` に保存

10. **SeverityLevel抽出**
    - Message内の `SeverityLevel=x` を抽出
    - 新規列 `SeverityLevel` を `protocol` と `Message` の間に挿入
    - 列: `Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, protocol, SeverityLevel, Message`
    - `severity_level_extracted/` に保存

11. **Severity抽出**
    - Message内の `Severity=xxx` を抽出
    - 新規列 `Severity` を `SeverityLevel` と `Message` の間に挿入
    - 列: `Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, protocol, SeverityLevel, Severity, Message`
    - `severity_extracted/` に保存

12. **CRITICAL抽出**
    - `Severity=CRITICAL` の行のみ抽出
    - `critical_only/` に保存

#### Phase 3: 最終出力

13. **最終マージ**（必要な場合のみ）
    - `critical_only/` 内に複数ファイルがあればマージ

14. **Excel出力**
    - フォント: 游ゴシック 11pt
    - 列幅: タイトル文字に合わせて自動調整
    - `final_output/` に保存

### プライベートIP判定ロジック

以下の範囲をprivateと判定：

- `10.0.0.0/8` → 10.0.0.0 ～ 10.255.255.255
- `172.16.0.0/12` → 172.16.0.0 ～ 172.31.255.255
- `192.168.0.0/16` → 192.168.0.0 ～ 192.168.255.255
- `127.0.0.0/8` → ループバック

上記以外はglobalと判定

### 出力仕様

#### 最終Excelフォーマット

**列構成**:
```
Timestamp, Hostname, AppName, routing, srcIP, judge, dstIP, judge, protocol, SeverityLevel, Severity, Message
```

**具体例**:
```
| Timestamp            | Hostname | AppName | routing                                 | srcIP         | judge   | dstIP        | judge  | protocol | SeverityLevel | Severity | Message                                                                                                                                 |
| -------------------- | -------- | ------- | --------------------------------------- | ------------- | ------- | ------------ | ------ | -------- | ------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 2025-12-16T00:46:22Z | srx-fw01 | RT_IDP  | 192.168.239.6/43657 > 80.86.112.63/8080 | 192.168.239.6 | private | 80.86.112.63 | global | udp      | 2             | CRITICAL | RT_IDP_ATTACK_LOG: SQL injection attack detected 192.168.239.6/43657 > 80.86.112.63/8080 protocol=udp SeverityLevel=2 Severity=CRITICAL |
```

#### Excelフォーマット

- **拡張子**: `.xlsx`
- **最大行数**: 800,000行（複数ファイルに分割されている場合あり）
- **フォント**: 游ゴシック 11pt
- **カラム幅**: タイトル文字に合わせて自動調整
- **ヘッダー**: 太字、背景色付き（オプション）

#### ファイル命名規則

```
filtered_2025-04-28_CRITICAL.xlsx              # 単一ファイルの場合
filtered_2025-04-28_CRITICAL_001.xlsx          # 分割時
filtered_2025-04-28_CRITICAL_002.xlsx
```

---

## 🚀 開発フェーズ

### 開発方針

**重要な原則**:
1. **1モジュールずつ開発**: 一度に複数モジュールを作らない
2. **都度確認**: 各モジュール完成後、動作確認
3. **段階的統合**: `run.py` に1つずつ組み込む
4. **テスト駆動**: 各モジュールに対してpytestを作成

### Phase 1: コアモジュール開発 + pytest ✅（現在）

**目標**: 各モジュールの基本機能を実装し、単体テストを作成  
**重要**: 1モジュールずつ実装し、都度 `run.py` に統合していく

#### タスク（開発順）

- [x] プロジェクト構成の決定
- [x] 設計書の作成

**ループ処理モジュール**
- [ ] `extract.py` の実装
  - [ ] ZIP展開機能（1ファイルずつ）
  - [ ] `test_extract.py` 作成
- [ ] `filter_keyword.py` の実装
  - [ ] キーワード抽出機能（RT_IDP_ATTACK）
  - [ ] `test_filter_keyword.py` 作成
- [ ] `cleanup_temp.py` の実装
  - [ ] ファイル削除機能
  - [ ] `test_cleanup_temp.py` 作成
- [ ] `run.py` に統合（ループ処理部分）

**マージ・変換モジュール**
- [ ] `merge_files.py` の実装
  - [ ] 80万行マージ機能
  - [ ] `test_merge_files.py` 作成
- [ ] `reduce_columns.py` の実装
  - [ ] 列削除機能
  - [ ] `test_reduce_columns.py` 作成
- [ ] `extract_routing.py` の実装
  - [ ] routing抽出機能
  - [ ] `test_extract_routing.py` 作成
- [ ] `split_ip.py` の実装
  - [ ] IP分離機能
  - [ ] `test_split_ip.py` 作成
- [ ] `classify_ip.py` の実装
  - [ ] IP判定機能（private/global）
  - [ ] `test_classify_ip.py` 作成
- [ ] `extract_protocol.py` の実装
  - [ ] protocol抽出機能
  - [ ] `test_extract_protocol.py` 作成
- [ ] `extract_severity_level.py` の実装
  - [ ] SeverityLevel抽出機能
  - [ ] `test_extract_severity_level.py` 作成
- [ ] `extract_severity.py` の実装
  - [ ] Severity抽出機能
  - [ ] `test_extract_severity.py` 作成
- [ ] `filter_critical.py` の実装
  - [ ] CRITICAL行抽出機能
  - [ ] `test_filter_critical.py` 作成

**最終出力モジュール**
- [ ] `final_merge.py` の実装
  - [ ] 最終マージ機能
  - [ ] `test_final_merge.py` 作成
- [ ] `export_excel.py` の実装
  - [ ] Excel出力機能
  - [ ] フォーマット調整
  - [ ] `test_export_excel.py` 作成
- [ ] `cleanup_all.py` の実装
  - [ ] 全ディレクトリクリーンアップ
  - [ ] `test_cleanup_all.py` 作成

---

### Phase 2: 統合テスト + 動作確認

**目標**: `run.py` で全パイプラインが正常に動作することを確認

#### タスク

- [ ] `run.py` の完成
  - [ ] 全モジュールの統合
  - [ ] エラーハンドリング
  - [ ] ロギング機能
- [ ] 統合テストの作成
  - [ ] エンドツーエンドテスト
  - [ ] パフォーマンステスト（10万行、100万行）
  - [ ] エラーケーステスト
- [ ] ドキュメント更新
  - [ ] README.md 作成
  - [ ] 使用方法の詳細記載
  - [ ] トラブルシューティング

---

### Phase 3: GUI実装

**目標**: フィルタ条件を直感的に設定できるGUIを追加

#### タスク

- [ ] GUI設計
  - [ ] ライブラリ選定（tkinter / PyQt）
  - [ ] 画面設計
- [ ] GUI実装
  - [ ] フィルタ条件入力画面
  - [ ] 実行ボタン
  - [ ] プログレスバー
  - [ ] ログ出力エリア
- [ ] GUIテスト
  - [ ] 動作確認
  - [ ] エラーケーステスト

---

### Phase 4: ショートカット化

**目標**: デスクトップアイコンからワンクリック起動

#### タスク

- [ ] .exeファイル化
  - [ ] PyInstaller設定
  - [ ] ビルドスクリプト作成
- [ ] ショートカット作成
  - [ ] アイコン設定
  - [ ] デスクトップ配置
- [ ] インストーラー作成（オプション）
  - [ ] Inno Setup等の検討

---

## 📦 技術スタック

### 必須ライブラリ

```python
pandas          # データ操作・CSV処理
openpyxl        # Excel読み書き
pytest          # テスティング
zipfile         # ZIP操作（標準ライブラリ）
pathlib         # パス操作（標準ライブラリ）
shutil          # ファイル操作（標準ライブラリ）
re              # 正規表現（標準ライブラリ）
```

### オプションライブラリ（Phase 3以降）

```python
tkinter         # GUI（標準ライブラリ）
PyQt5           # GUI（高機能版、オプション）
pyinstaller     # .exe化
```

### 開発環境

- **Python**: 3.8以上推奨
- **OS**: Windows 10/11
- **IDE**: VSCode
- **Terminal**: PowerShell
- **パッケージマネージャ**: uv（高速なpip代替）
- **仮想環境**: venv
- **メモリ**: 4GB以上推奨（100万行処理時）

---

## 🛠️ 開発環境セットアップ

### 前提条件

以下がインストール済みであること：
- Python 3.8以上
- Git
- VSCode

### 1. uvのインストール

uvはRust製の超高速Pythonパッケージマネージャーです（pipの10-100倍高速）。

#### PowerShellでインストール

```powershell
# uvをインストール
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# インストール確認
uv --version
```

### 2. プロジェクトのセットアップ

```powershell
# プロジェクトディレクトリ作成
mkdir juniper-syslog-filter
cd juniper-syslog-filter

# Gitリポジトリ初期化
git init

# .gitignoreを作成
@"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/
env/

# IDE
.vscode/
.idea/

# データディレクトリ
source_logs/
temp_extracted/
filtered_logs/
merged_logs/
columns_reduced/
routing_added/
ip_split/
ip_classified/
protocol_extracted/
severity_level_extracted/
severity_extracted/
critical_only/
final_output/

# テスト
.pytest_cache/
.coverage
htmlcov/

# その他
*.log
*.xlsx
*.csv
*.zip
"@ | Out-File -FilePath .gitignore -Encoding utf8
```

### 3. 仮想環境の作成

```powershell
# venv仮想環境を作成
python -m venv venv

# 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# 有効化されると、プロンプトに(venv)が表示される
# (venv) PS C:\path\to\juniper-syslog-filter>
```

> **注意**: PowerShellでスクリプト実行ポリシーエラーが出る場合：
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. 必要なパッケージのインストール（uvを使用）

```powershell
# 仮想環境内でuvを使ってインストール
uv pip install pandas openpyxl pytest

# requirements.txtを作成（後で使用）
uv pip freeze > requirements.txt
```

**uvのメリット**:
- **速度**: pipの10-100倍高速
- **互換性**: pip完全互換のコマンド
- **依存解決**: より高速で正確

### 5. プロジェクト構造の作成

```powershell
# ディレクトリ構造を作成
mkdir modules, tests, source_logs, docs

# 空の__init__.pyを作成
New-Item -Path "modules\__init__.py" -ItemType File
New-Item -Path "tests\__init__.py" -ItemType File

# run.pyの雛形を作成
@"
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Juniper Syslog Filter - Main Pipeline
"""

def main():
    print("Juniper Syslog Filter - Starting...")
    # TODO: モジュールを順次実装

if __name__ == "__main__":
    main()
"@ | Out-File -FilePath run.py -Encoding utf8
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
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.encoding": "utf8"
}
```

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

---

## 📖 使用方法

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
│   ├── filter_critical.py            # CRITICAL抽出
│   │
│   ├── # 最終出力モジュール
│   ├── final_merge.py                # 最終マージ
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
│   ├── test_filter_critical.py
│   ├── test_final_merge.py
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

### ソフトスキル

- **問題発見力**: 「当たり前」に疑問を持つ
- **GPT活用**: 学習パートナーとしての活用
- **ユーザー視点**: オペレーターの作業負担を考慮した設計

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

| 日付       | バージョン | 内容                                                        |
| ---------- | ---------- | ----------------------------------------------------------- |
| 2025-12-16 | 1.0.0      | 初版作成・設計書完成                                        |
| 2025-12-16 | 1.1.0      | 詳細な処理フロー反映・14モジュール構成に更新                |
| 2025-12-16 | 1.2.0      | 開発環境セットアップ追加（uv + venv + VSCode + PowerShell） |

---
