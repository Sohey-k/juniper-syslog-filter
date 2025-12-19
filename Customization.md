# Juniper Syslog Filter - 改造・カスタマイズガイド

本ドキュメントは、このツールを他の環境や他社製品に転用する際のガイドです。

---

## 📋 目次

1. [ハードコード箇所の完全リスト](#ハードコード箇所の完全リスト)
2. [データ構造分析ガイド](#データ構造分析ガイド)
3. [実践カスタマイズ例](#実践カスタマイズ例)
4. [設定ファイル化の方法](#設定ファイル化の方法)
5. [トラブルシューティング](#トラブルシューティング)

---

## 🔍 ハードコード箇所の完全リスト

### Phase 1: ループ処理モジュール

#### 1. filter_keyword.py
```python
# ハードコード箇所
keyword = "RT_IDP_ATTACK"

# 変更例
keyword = "RT_SCREEN"        # 他のアプリケーション
keyword = "RT_FLOW"          # フローログ
keyword = "SSH"              # SSH関連ログ
```

**影響範囲**: フィルタリング対象が変わる  
**変更難易度**: ★☆☆☆☆（簡単）

---

### Phase 2-3: マージ・列削減

#### 2. merge_files.py
```python
# ハードコード箇所
max_rows = 800000  # 80万行単位でファイル分割

# 変更例
max_rows = 500000   # 50万行に変更（メモリ節約）
max_rows = 1000000  # 100万行に変更（Excel上限考慮）
```

**影響範囲**: 出力ファイル数が変わる  
**変更難易度**: ★☆☆☆☆（簡単）

#### 3. reduce_columns.py
```python
# ハードコード箇所
keep_columns = [0, 1, 2, 6]  # Timestamp, Hostname, AppName, Message

# 列インデックスの意味
# 0: Timestamp
# 1: Hostname
# 2: AppName
# 3: SeverityLevel（削除）
# 4: Severity（削除）
# 5: LogType（削除）
# 6: Message

# 変更例
keep_columns = [0, 1, 2, 4, 6]  # Severityも残す場合
keep_columns = [0, 2, 6]        # Hostnameを削除する場合
```

**影響範囲**: 以降の全モジュールに影響  
**変更難易度**: ★★☆☆☆（注意が必要）

---

### Phase 4-6: データ抽出・分割

#### 4. extract_routing.py
```python
# ハードコード箇所
pattern1 = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+ > (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+'
pattern2 = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) > (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'

# Juniper SRX固有のパターン
# 例: "192.168.1.5/12345 > 203.0.113.10/80"

# 他社製品での例
# Cisco ASA: "192.168.1.5:12345 -> 203.0.113.10:80"
# 変更例
pattern1 = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+ -> (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+'
```

**影響範囲**: routing列の抽出結果  
**変更難易度**: ★★★☆☆（正規表現の知識が必要）

#### 5. split_ip.py
```python
# ハードコード箇所
delimiter = ' > '  # Juniper SRX形式

# 変更例
delimiter = ' -> '  # Cisco ASA形式
delimiter = ','     # カンマ区切り
```

**影響範囲**: srcIP/dstIP の分割  
**変更難易度**: ★☆☆☆☆（簡単）

#### 6. classify_ip.py
```python
# ハードコード箇所（プライベートIP範囲）
# 10.0.0.0/8
# 172.16.0.0/12
# 192.168.0.0/16

# 変更不要（RFC1918準拠）
# カスタムプライベートネットワークがあれば追加可能
```

**影響範囲**: IP分類結果  
**変更難易度**: ★★☆☆☆（IPネットワークの知識が必要）

---

### Phase 7-9: Message内データ抽出

#### 7. extract_protocol.py
```python
# ハードコード箇所
pattern = r'protocol=(\w+)'

# Juniper SRX: "protocol=tcp"
# 他社製品での例
# Cisco ASA: "Protocol: TCP"
pattern = r'Protocol:\s+(\w+)'

# Palo Alto: "proto=6"（数値）
pattern = r'proto=(\d+)'
```

**影響範囲**: protocol列の抽出結果  
**変更難易度**: ★★★☆☆（正規表現 + データ構造の理解）

#### 8. extract_severity_level.py
```python
# ハードコード箇所
pattern = r'SeverityLevel=(\d+)'

# Juniper SRX: "SeverityLevel=2"
# 他社製品での例
# Cisco ASA: "Severity: 2"
pattern = r'Severity:\s+(\d+)'

# Palo Alto: "severity=critical"（文字列）
pattern = r'severity=(\w+)'
```

**影響範囲**: SeverityLevel列の抽出結果  
**変更難易度**: ★★★☆☆（正規表現 + データ構造の理解）

#### 9. extract_severity.py
```python
# ハードコード箇所
pattern = r'Severity=(\w+)'

# Juniper SRX: "Severity=CRITICAL"
# 他社製品での例
# Cisco ASA: "Severity: Critical"
pattern = r'Severity:\s+(\w+)'

# Palo Alto: "severity-level=critical"
pattern = r'severity-level=(\w+)'
```

**影響範囲**: Severity列の抽出結果  
**変更難易度**: ★★★☆☆（正規表現 + データ構造の理解）

---

### Phase 10-11: フィルタ・出力

#### 10. filter_critical_and_merge.py
```python
# ハードコード箇所
severity_filter = "CRITICAL"

# 変更例
severity_filter = "WARNING"           # WARNING以上
severity_filter = ["CRITICAL", "WARNING"]  # 複数条件（要改造）
```

**影響範囲**: 最終出力される行数  
**変更難易度**: ★☆☆☆☆（簡単）

#### 11. export_excel.py
```python
# ハードコード箇所
font_name = "游ゴシック"
font_size = 11

# 変更例
font_name = "Arial"           # 英語環境
font_name = "MS Gothic"       # 等幅フォント
font_size = 10                # サイズ変更
```

**影響範囲**: Excel出力の見た目  
**変更難易度**: ★☆☆☆☆（簡単）

---

## 📊 データ構造分析ガイド

他社製品や異なるログ形式に対応する手順です。

### ステップ1: サンプルログの取得

```powershell
# 対象システムから数時間分のログを取得
# 例: sample_log.csv
```

### ステップ2: CSV構造の確認

```python
import pandas as pd

# CSVを読み込み
df = pd.read_csv("sample_log.csv", encoding='utf-8', nrows=10)

# 列名を確認
print("列名:")
print(df.columns.tolist())

# サンプルデータを表示
print("\nサンプル:")
print(df.head())
```

**出力例（Juniper SRX）:**
```
列名:
['Timestamp', 'Hostname', 'AppName', 'SeverityLevel', 'Severity', 'LogType', 'Message']

サンプル:
                 Timestamp  Hostname AppName  SeverityLevel Severity LogType                    Message
0  2025-12-19T10:00:00Z  srx-fw01  RT_IDP              2  CRITICAL  THREAT  RT_IDP_ATTACK_LOG: ...
```

### ステップ3: Message列のパターン分析

```python
# Message列の内容を確認
for msg in df['Message'].head(20):
    print(msg)
    print("-" * 80)
```

**分析ポイント:**
1. IPアドレスの記述方法は？（`192.168.1.5/80` or `192.168.1.5:80`）
2. プロトコルの記述は？（`protocol=tcp` or `Proto: TCP`）
3. Severityの記述は？（`Severity=CRITICAL` or `Level: Critical`）

### ステップ4: 正規表現パターンの作成

```python
import re

# サンプルメッセージ
message = "RT_IDP_ATTACK_LOG: Attack detected 192.168.1.5/12345 > 203.0.113.10/80 protocol=tcp SeverityLevel=2 Severity=CRITICAL"

# パターンテスト
pattern = r'protocol=(\w+)'
match = re.search(pattern, message)
if match:
    print(f"抽出結果: {match.group(1)}")  # tcp
else:
    print("マッチしませんでした")
```

### ステップ5: テストデータの作成

```python
# scripts/generate_sample_data.py を改造して
# 新しいログ形式のテストデータを生成
```

---

## 🛠️ 実践カスタマイズ例

### 例1: キーワードを変更（RT_SCREEN）

**変更箇所**: `run.py` のPhase 1

```python
# 変更前
filtered_count = filter_keyword(
    extracted_csvs, filtered_dir, keyword="RT_IDP_ATTACK"
)

# 変更後
filtered_count = filter_keyword(
    extracted_csvs, filtered_dir, keyword="RT_SCREEN"
)
```

### 例2: WARNING以上を抽出

**変更箇所**: `modules/filter_critical_and_merge.py`

```python
# 変更前
def filter_and_merge_critical(input_files, output_file, verbose=True):
    critical_df = df[df['Severity'] == 'CRITICAL']

# 変更後
def filter_and_merge_critical(input_files, output_file, verbose=True):
    # WARNING以上を抽出
    critical_df = df[df['Severity'].isin(['CRITICAL', 'WARNING'])]
```

### 例3: Cisco ASA形式に対応

**変更箇所**: `modules/extract_routing.py`

```python
# 変更前（Juniper SRX）
pattern1 = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+ > (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+'

# 変更後（Cisco ASA: "192.168.1.5:12345 -> 203.0.113.10:80"）
pattern1 = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+ -> (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+'
```

**変更箇所**: `modules/split_ip.py`

```python
# 変更前
delimiter = ' > '

# 変更後
delimiter = ' -> '
```

---

## ⚙️ 設定ファイル化の方法

ハードコード値を外部ファイルに移動する方法です。

### config.yaml の作成

```yaml
# config.yaml
filter:
  keyword: "RT_IDP_ATTACK"
  severity: "CRITICAL"

merge:
  max_rows: 800000

columns:
  keep: [0, 1, 2, 6]  # Timestamp, Hostname, AppName, Message

patterns:
  routing:
    pattern1: '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+ > (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d+'
    pattern2: '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) > (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    delimiter: ' > '
  protocol: 'protocol=(\w+)'
  severity_level: 'SeverityLevel=(\d+)'
  severity: 'Severity=(\w+)'

excel:
  font_name: "游ゴシック"
  font_size: 11
```

### config読み込みモジュールの作成

```python
# modules/config_loader.py
import yaml
from pathlib import Path

def load_config(config_path='config.yaml'):
    """設定ファイルを読み込む"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 使用例
config = load_config()
keyword = config['filter']['keyword']
max_rows = config['merge']['max_rows']
```

### モジュールの改造例

```python
# modules/filter_keyword.py の改造版
from modules.config_loader import load_config

def filter_keyword(input_files, output_dir, keyword=None, verbose=True):
    # keywordが指定されていない場合、configから読み込み
    if keyword is None:
        config = load_config()
        keyword = config['filter']['keyword']
    
    # 既存の処理...
```

### 必要なパッケージ

```powershell
uv pip install pyyaml
```

---

## 🐛 トラブルシューティング

### 問題1: 正規表現がマッチしない

**症状**: 抽出列が空になる

```python
# デバッグ方法
import pandas as pd

df = pd.read_csv("input.csv", encoding='utf-8')

# サンプルメッセージを表示
print(df['Message'].head(10))

# パターンマッチをテスト
pattern = r'protocol=(\w+)'
result = df['Message'].str.extract(pattern, expand=False)
print(result.head(10))
print(f"マッチした行数: {result.notna().sum()}")
```

**対策**:
1. Messageの実際の形式を確認
2. パターンを調整
3. テストデータで検証

### 問題2: 列インデックスがずれる

**症状**: `KeyError: 'Message'` や列が正しく取得できない

**原因**: `reduce_columns.py` で削除した列の影響

```python
# 削除する列を変更した場合、以降のモジュールで列名を確認
df = pd.read_csv("reduced_logs/file.csv")
print(df.columns.tolist())  # 実際の列名を確認
```

**対策**:
1. 列名で参照する（インデックスではなく）
2. 各モジュールで列の存在確認を追加

### 問題3: エンコーディングエラー

**症状**: `UnicodeDecodeError`

```python
# 変更前
df = pd.read_csv(input_path, encoding='utf-8')

# 変更後（Shift_JISの場合）
df = pd.read_csv(input_path, encoding='shift_jis')

# 変更後（自動判定）
df = pd.read_csv(input_path, encoding='utf-8', errors='ignore')
```

### 問題4: メモリ不足

**症状**: `MemoryError` or 処理が遅い

**対策1**: マージ最大行数を減らす
```python
# merge_files.py
max_rows = 500000  # 80万から50万に変更
```

**対策2**: チャンク処理に変更
```python
# 大きなファイルをチャンクで読み込む
chunks = pd.read_csv(input_path, chunksize=100000)
for chunk in chunks:
    # 処理
    pass
```

---

## 📚 参考情報

### 主要な正規表現パターン

```python
# IPv4アドレス
r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

# IPv4アドレス + ポート（Juniper形式）
r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d+'

# IPv4アドレス + ポート（Cisco形式）
r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+'

# プロトコル（英数字）
r'protocol=(\w+)'
r'Proto:\s+(\w+)'

# Severity（英大文字）
r'Severity=([A-Z]+)'
r'severity:\s+([a-z]+)'

# 数値
r'Level=(\d+)'
r'level:\s+(\d+)'
```

### 他社製品のログ形式例

#### Cisco ASA
```
Dec 19 2025 10:00:00: %ASA-2-106001: Inbound TCP connection denied from 192.168.1.5:12345 -> 203.0.113.10:80 flags SYN
```

#### Palo Alto
```
1,2025/12/19 10:00:00,012345,THREAT,url,2049,2025/12/19 10:00:00,192.168.1.5,203.0.113.10,...
```

#### Fortinet
```
date=2025-12-19 time=10:00:00 devname="FGT60E" logid="0000000013" type="traffic" subtype="forward" level="notice" srcip=192.168.1.5 dstip=203.0.113.10 proto=6
```

---

## ✅ カスタマイズチェックリスト

改造時の確認項目：

- [ ] サンプルログを入手してデータ構造を確認した
- [ ] 正規表現パターンをテストした
- [ ] テストデータを作成した
- [ ] 各モジュールの単体テストを実行した
- [ ] 統合テスト（run.py）を実行した
- [ ] 出力ファイルの内容を確認した
- [ ] エラーログを確認した
- [ ] 処理時間を計測した
- [ ] 変更箇所をドキュメント化した

---

## 🔮 将来の拡張アイデア

### 1. 設定プロファイル管理
```yaml
# profiles/juniper_srx.yaml
# profiles/cisco_asa.yaml
# profiles/palo_alto.yaml
```

### 2. GUI化
```python
# 設定をGUIで選択
- プロファイル選択
- パラメータ入力
- モジュール選択
```

### 3. プラグイン化
```python
# plugins/custom_parser.py
# 独自パーサーを追加可能に
```

---

## 📝 ライセンス

MIT License - 自由にカスタマイズしてください

---

## 👤 作成者

**Sohey-k**
- GitHub: https://github.com/Sohey-k

---

最終更新: 2025-12-19