# 📊 Stock Technical Analyzer
株価テクニカル分析ツール

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_UI-ff4b4b.svg)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-pink.svg)](https://github.com/sponsors/Zeur5-6)

## ✨ 特徴

- 📈 **移動平均線** (SMA 10日, 30日, 60日)
- 📊 **RSI** (Relative Strength Index) — 買われすぎ・売られすぎ判定
- 📉 **MACD** — モメンタム分析（正負色分けヒストグラム付き）
- 🎯 **ボリンジャーバンド** — 価格変動幅の可視化
- 📦 **出来高チャート** — 売買量の推移
- 🌙 **ダークテーマ** — 洗練されたプロ仕様のデザイン
- 🔄 **複数銘柄比較** — 正規化価格、RSI、リターン比較
- 🌐 **Streamlit Web UI** — ブラウザで操作できるダッシュボード
- 📋 **自動レポート生成** — テキスト形式の分析レポート

## 🚀 クイックスタート

### インストール
```bash
git clone https://github.com/Zeur5-6/stock_analyzer.git
cd stock_analyzer
pip install -r requirements.txt
```

### CLI で使う
```bash
# 単一銘柄分析
python stock_analyzer.py AAPL 1mo

# 複数銘柄比較
python stock_analyzer.py AAPL,TSLA,GOOGL 3mo
```

### Web UI で使う
```bash
streamlit run app.py
```
ブラウザが自動で開き、インタラクティブなダッシュボードが表示されます。

## 📖 パラメータ

| パラメータ | 説明 | 例 |
|---|---|---|
| **TICKER** | ティッカーシンボル（カンマ区切りで複数可） | `AAPL`, `TSLA,GOOGL` |
| **PERIOD** | 分析期間 | `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max` |

## 📂 出力

分析結果は `output/` フォルダに自動保存されます:
- `output/[TICKER]_analysis_[日時].png` — テクニカル分析チャート
- `output/[TICKER]_report_[日時].txt` — 分析レポート
- `output/compare_[TICKERS]_[日時].png` — 比較チャート（複数銘柄時）

## 📊 テクニカル指標の解説

| 指標 | 説明 |
|---|---|
| **SMA** | 短期(10日)が長期(30日)の上 → 上昇トレンド |
| **RSI** | 70超 = 買われすぎ / 30未満 = 売られすぎ |
| **MACD** | MACDがシグナル線を上抜け → 買いシグナル |
| **ボリンジャーバンド** | バンド外に価格が出ると反発の可能性 |

## 🛠️ 技術情報

- Python 3.11+
- yfinance — Yahoo Finance APIラッパー
- pandas — データ処理
- matplotlib — チャート可視化
- numpy — 数値計算
- streamlit — Web UIフレームワーク
- mplfinance — 金融チャート（オプション）

## ⚠️ 免責事項

このツールは**教育目的**であり、投資助言ではありません。
実際の投資決定は自己責任で行ってください。
過去のパフォーマンスが将来の結果を保証するものではありません。

## 📄 ライセンス

MIT License — [LICENSE](LICENSE) を参照
