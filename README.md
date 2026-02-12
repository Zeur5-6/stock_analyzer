# 📊 Stock Technical Analyzer
株価チE��ニカル刁E��チE�Eル

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_UI-ff4b4b.svg)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-pink.svg)](https://github.com/sponsors/Zeur5-6)

## ✨ 特徴

- 📈 **移動平坁E��E* (SMA 10日, 30日, 60日)
- 📊 **RSI** (Relative Strength Index)  E買われすぎ・売られすぎ判宁E- 📉 **MACD**  Eモメンタム刁E���E�正負色刁E��ヒストグラム付き�E�E- 🎯 **ボリンジャーバンチE*  E価格変動幁E�E可視化
- 📦 **出来高チャーチE*  E売買量�E推移
- 🌙 **ダークチE�EチE*  E洗練された�Eロ仕様�EチE��イン
- 🔄 **褁E��銘柄比輁E*  E正規化価格、RSI、リターン比輁E- 🌐 **Streamlit Web UI**  Eブラウザで操作できるダチE��ュボ�EチE- 📋 **自動レポ�Eト生戁E*  EチE��スト形式�E刁E��レポ�EチE
## 🚀 クイチE��スターチE
### インスト�Eル
```bash
git clone https://github.com/Zeur5-6/stock_analyzer.git
cd stock_analyzer
pip install -r requirements.txt
```

### CLI で使ぁE```bash
# 単一銘柄刁E��
python stock_analyzer.py AAPL 1mo

# 褁E��銘柄比輁Epython stock_analyzer.py AAPL,TSLA,GOOGL 3mo
```

### Web UI で使ぁE```bash
streamlit run app.py
```
ブラウザが�E動で開き、インタラクチE��ブなダチE��ュボ�Eドが表示されます、E
## 📖 パラメータ

| パラメータ | 説昁E| 侁E|
|---|---|---|
| **TICKER** | チE��チE��ーシンボル�E�カンマ区刁E��で褁E��可�E�E| `AAPL`, `TSLA,GOOGL` |
| **PERIOD** | 刁E��期間 | `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max` |

## 📂 出劁E
刁E��結果は `output/` フォルダに自動保存されまぁE
- `output/[TICKER]_analysis_[日晁E.png`  EチE��ニカル刁E��チャーチE- `output/[TICKER]_report_[日晁E.txt`  E刁E��レポ�EチE- `output/compare_[TICKERS]_[日晁E.png`  E比輁E��ャート（褁E��銘柄時！E
## 📊 チE��ニカル持E���E解説

| 持E��E| 説昁E|
|---|---|
| **SMA** | 短朁E10日)が長朁E30日)の丁EↁE上�EトレンチE|
| **RSI** | 70趁E= 買われすぎ / 30未満 = 売られすぎ |
| **MACD** | MACDがシグナル線を上抜ぁEↁE買ぁE��グナル |
| **ボリンジャーバンチE* | バンド外に価格が�Eると反発の可能性 |

## 🛠�E�E技術情報

- Python 3.11+
- yfinance  EYahoo Finance APIラチE��ー
- pandas  EチE�Eタ処琁E- matplotlib  Eチャート可視化
- numpy  E数値計箁E- streamlit  EWeb UIフレームワーク
- mplfinance  E金融チャート（オプション�E�E
## ⚠�E�E免責事頁E
こ�EチE�Eルは**教育目皁E*であり、投賁E��言ではありません、E実際の投賁E��定�E自己責任で行ってください、E過去のパフォーマンスが封E��の結果を保証するも�Eではありません、E
## 📄 ライセンス

MIT License  E[LICENSE](LICENSE) を参照
