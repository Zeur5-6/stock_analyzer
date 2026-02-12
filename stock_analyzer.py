#!/usr/bin/env python3
"""
Stock Technical Analyzer
株価テクニカル分析ツール

Yahoo Financeの公開データを使用して、株価のテクニカル分析を行い、
移動平均線、ボラティリティ、トレンドを可視化します。

使用法:
    python stock_analyzer.py [TICKER] [PERIOD]

例:
    python stock_analyzer.py AAPL 1mo    # Apple, 1ヶ月
    python stock_analyzer.py TSLA 3mo    # Tesla, 3ヶ月
    python stock_analyzer.py GOOGL 6mo   # Google, 6ヶ月
    python stock_analyzer.py AAPL,TSLA,GOOGL 3mo  # 複数銘柄比較

制約事項（厳守）:
- 読み取り専用Webアクセス（会員登録・送信なし）
- ローカルフォルダのみ使用
- 実際の売買は行わず分析のみ
- time.sleep(3) でAPI制限を遵守
"""

import time
import sys
import os
from datetime import datetime
from pathlib import Path
import argparse

# データ取得と分析
try:
    import yfinance as yf
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.style import use
    import numpy as np
except ImportError as e:
    print("エラー: 必要なライブラリがありません")
    print(f"詳細: {e}")
    print("インストール: pip install yfinance pandas matplotlib numpy")
    sys.exit(1)

# mplfinance はオプション（ローソク足チャート用）
try:
    import mplfinance as mpf
    HAS_MPLFINANCE = True
except ImportError:
    HAS_MPLFINANCE = False

# ─── 定数 ─────────────────────────────────────────────────
VALID_PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
OUTPUT_DIR = Path('./output')

# ─── カラーパレット ─────────────────────────────────────────
COLORS = {
    'bg':         '#1a1a2e',
    'panel':      '#16213e',
    'grid':       '#2a2a4a',
    'text':       '#e0e0e0',
    'accent':     '#00d4ff',
    'price':      '#00d4ff',
    'sma10':      '#ff6b6b',
    'sma30':      '#ffd93d',
    'sma60':      '#6bcb77',
    'bb_fill':    '#00d4ff',
    'rsi':        '#ff6b6b',
    'macd':       '#00d4ff',
    'signal':     '#ff6b6b',
    'vol_up':     '#00c853',
    'vol_down':   '#ff1744',
    'hist_pos':   '#00c853',
    'hist_neg':   '#ff1744',
    'overbought': '#ff6b6b',
    'oversold':   '#6bcb77',
}

# ─── 日本語フォント設定 ────────────────────────────────────
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'Segoe UI Symbol', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def ensure_output_dir():
    """出力ディレクトリを作成"""
    OUTPUT_DIR.mkdir(exist_ok=True)


class StockAnalyzer:
    """株価テクニカル分析クラス"""

    def __init__(self, ticker, period='1mo'):
        """
        初期化

        Args:
            ticker: ティッカーシンボル (例: AAPL, TSLA, GOOGL)
            period: 期間 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        """
        self.ticker = ticker.upper()
        self.period = period
        self.data = None
        self.technical_indicators = {}

        # 期間バリデーション
        if self.period not in VALID_PERIODS:
            print(f"⚠️  無効な期間: '{self.period}'")
            print(f"   有効な値: {', '.join(VALID_PERIODS)}")
            suggestion = self._suggest_period(self.period)
            if suggestion:
                print(f"   → もしかして: '{suggestion}' ?")
            sys.exit(1)

    @staticmethod
    def _suggest_period(invalid):
        """無効な期間に対する候補を提案"""
        mapping = {'1m': '1mo', '3m': '3mo', '6m': '6mo'}
        return mapping.get(invalid)

    def fetch_data(self):
        """Yahoo Financeから株価データを取得"""
        print(f"  ⏳ {self.ticker} のデータを取得中...")

        try:
            stock = yf.Ticker(self.ticker)
            self.data = stock.history(period=self.period)

            if self.data.empty:
                print(f"  ❌ {self.ticker} のデータが見つかりません")
                return False

            print(f"  ✅ データ取得完了: {len(self.data)}件 "
                  f"({self.data.index[0].strftime('%Y-%m-%d')} ~ "
                  f"{self.data.index[-1].strftime('%Y-%m-%d')})")
            return True

        except Exception as e:
            print(f"  ❌ データ取得エラー: {e}")
            return False

    def calculate_technical_indicators(self):
        """テクニカル指標を計算"""

        # 1. 移動平均線
        self.data['SMA_10'] = self.data['Close'].rolling(window=10).mean()
        self.data['SMA_30'] = self.data['Close'].rolling(window=30).mean()
        self.data['SMA_60'] = self.data['Close'].rolling(window=60).mean()

        # 2. ボラティリティ（標準偏差）
        self.data['Volatility'] = self.data['Close'].rolling(window=20).std()

        # 3. RSI (Relative Strength Index)
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

        # 4. MACD
        exp1 = self.data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = self.data['Close'].ewm(span=26, adjust=False).mean()
        self.data['MACD'] = exp1 - exp2
        self.data['Signal'] = self.data['MACD'].ewm(span=9, adjust=False).mean()
        self.data['Histogram'] = self.data['MACD'] - self.data['Signal']

        # 5. ボリンジャーバンド
        bb_period = 20
        bb_std = 2
        self.data['BB_Middle'] = self.data['Close'].rolling(window=bb_period).mean()
        bb_std_dev = self.data['Close'].rolling(window=bb_period).std()
        self.data['BB_Upper'] = self.data['BB_Middle'] + (bb_std_dev * bb_std)
        self.data['BB_Lower'] = self.data['BB_Middle'] - (bb_std_dev * bb_std)

        # 6. 日次リターン
        self.data['Daily_Return'] = self.data['Close'].pct_change() * 100

        print(f"  ✅ テクニカル指標計算完了")

    def analyze_trend(self):
        """トレンド分析"""
        latest_price = self.data['Close'].iloc[-1]
        sma_10 = self.data['SMA_10'].iloc[-1]
        sma_30 = self.data['SMA_30'].iloc[-1]
        rsi = self.data['RSI'].iloc[-1]
        macd = self.data['MACD'].iloc[-1]
        signal = self.data['Signal'].iloc[-1]

        # トレンド判定
        if latest_price > sma_10 > sma_30:
            trend = "強い上昇トレンド (Strong Bullish)"
            trend_emoji = "📈"
            trend_color = COLORS['vol_up']
        elif latest_price > sma_10:
            trend = "上昇トレンド (Moderately Bullish)"
            trend_emoji = "📊"
            trend_color = COLORS['sma60']
        elif latest_price < sma_10 < sma_30:
            trend = "強い下降トレンド (Strong Bearish)"
            trend_emoji = "📉"
            trend_color = COLORS['vol_down']
        elif latest_price < sma_10:
            trend = "下降トレンド (Moderately Bearish)"
            trend_emoji = "📉"
            trend_color = COLORS['sma10']
        else:
            trend = "横ばい (Sideways)"
            trend_emoji = "➡️"
            trend_color = COLORS['text']

        # RSI分析
        if rsi > 70:
            rsi_signal = "買われすぎ (Overbought)"
        elif rsi < 30:
            rsi_signal = "売られすぎ (Oversold)"
        else:
            rsi_signal = "中立 (Neutral)"

        # MACD分析
        if macd > signal:
            macd_signal = "買いシグナル (Bullish)"
        else:
            macd_signal = "売りシグナル (Bearish)"

        # 価格変動率
        period_return = ((latest_price / self.data['Close'].iloc[0]) - 1) * 100

        return {
            'trend': trend,
            'trend_emoji': trend_emoji,
            'trend_color': trend_color,
            'latest_price': latest_price,
            'sma_10': sma_10,
            'sma_30': sma_30,
            'rsi': rsi,
            'rsi_signal': rsi_signal,
            'macd': macd,
            'signal': signal,
            'macd_signal': macd_signal,
            'period_return': period_return,
            'volatility': self.data['Volatility'].iloc[-1],
            'high': self.data['High'].max(),
            'low': self.data['Low'].min(),
            'avg_volume': self.data['Volume'].mean(),
        }

    def plot_chart(self):
        """ダークテーマの洗練されたチャートを描画して保存"""
        print(f"  🎨 チャートを生成中...")

        fig, axes = plt.subplots(4, 1, figsize=(14, 16),
                                 gridspec_kw={'height_ratios': [3, 1, 1.5, 1.5]})
        fig.patch.set_facecolor(COLORS['bg'])

        for ax in axes:
            ax.set_facecolor(COLORS['panel'])
            ax.tick_params(colors=COLORS['text'], labelsize=9)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color(COLORS['grid'])
            ax.spines['left'].set_color(COLORS['grid'])
            ax.grid(True, alpha=0.15, color=COLORS['grid'], linestyle='--')

        analysis = self.analyze_trend()

        # ─── タイトル ────────────────────────────────────
        fig.suptitle(f'{self.ticker} テクニカル分析',
                     fontsize=20, fontweight='bold', color=COLORS['text'], y=0.995)
        fig.text(0.5, 0.97,
                 f'${analysis["latest_price"]:.2f}  |  {analysis["trend"]}  |  '
                 f'期間リターン: {analysis["period_return"]:+.2f}%',
                 ha='center', fontsize=11, color=COLORS['accent'], alpha=0.85)

        # ─── グラフ1: 価格チャート ────────────────────────
        ax1 = axes[0]
        ax1.plot(self.data.index, self.data['Close'],
                 label='終値', color=COLORS['price'], linewidth=2, zorder=5)
        ax1.plot(self.data.index, self.data['SMA_10'],
                 label='SMA 10', color=COLORS['sma10'], alpha=0.8, linewidth=1.2)
        ax1.plot(self.data.index, self.data['SMA_30'],
                 label='SMA 30', color=COLORS['sma30'], alpha=0.8, linewidth=1.2)

        # ボリンジャーバンド
        ax1.fill_between(self.data.index, self.data['BB_Upper'], self.data['BB_Lower'],
                         alpha=0.08, color=COLORS['bb_fill'], label='Bollinger Bands')
        ax1.plot(self.data.index, self.data['BB_Upper'],
                 color=COLORS['bb_fill'], alpha=0.3, linewidth=0.8, linestyle='--')
        ax1.plot(self.data.index, self.data['BB_Lower'],
                 color=COLORS['bb_fill'], alpha=0.3, linewidth=0.8, linestyle='--')

        ax1.set_ylabel('価格 (USD)', fontsize=10, color=COLORS['text'])
        ax1.set_title('価格・移動平均線・ボリンジャーバンド', fontsize=12,
                       fontweight='bold', color=COLORS['text'], pad=10)
        ax1.legend(loc='upper left', fontsize=8, facecolor=COLORS['panel'],
                   edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=0)

        # ─── グラフ2: 出来高 ────────────────────────────
        ax2 = axes[1]
        colors_vol = [COLORS['vol_up'] if self.data['Close'].iloc[i] >= self.data['Open'].iloc[i]
                      else COLORS['vol_down'] for i in range(len(self.data))]
        ax2.bar(self.data.index, self.data['Volume'], color=colors_vol, alpha=0.7, width=0.8)
        ax2.set_ylabel('出来高', fontsize=10, color=COLORS['text'])
        ax2.set_title('出来高 (Volume)', fontsize=12, fontweight='bold',
                       color=COLORS['text'], pad=10)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.0f}M'))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=0)

        # ─── グラフ3: RSI ────────────────────────────────
        ax3 = axes[2]
        ax3.plot(self.data.index, self.data['RSI'],
                 label='RSI', color=COLORS['rsi'], linewidth=1.5)
        ax3.axhline(y=70, color=COLORS['overbought'], linestyle='--', alpha=0.6,
                     label='買われすぎ (70)')
        ax3.axhline(y=30, color=COLORS['oversold'], linestyle='--', alpha=0.6,
                     label='売られすぎ (30)')
        ax3.axhspan(70, 100, alpha=0.05, color=COLORS['overbought'])
        ax3.axhspan(0, 30, alpha=0.05, color=COLORS['oversold'])
        ax3.set_ylabel('RSI', fontsize=10, color=COLORS['text'])
        ax3.set_title('相対力指数 (RSI)', fontsize=12, fontweight='bold',
                       color=COLORS['text'], pad=10)
        ax3.set_ylim([0, 100])
        ax3.legend(loc='upper left', fontsize=8, facecolor=COLORS['panel'],
                   edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=0)

        # ─── グラフ4: MACD ───────────────────────────────
        ax4 = axes[3]
        ax4.plot(self.data.index, self.data['MACD'],
                 label='MACD', color=COLORS['macd'], linewidth=1.5)
        ax4.plot(self.data.index, self.data['Signal'],
                 label='Signal', color=COLORS['signal'], linewidth=1.5)

        # ヒストグラム（正負で色分け）
        hist = self.data['Histogram']
        ax4.bar(self.data.index, hist.where(hist >= 0), color=COLORS['hist_pos'],
                alpha=0.5, width=0.8, label='Histogram (+)')
        ax4.bar(self.data.index, hist.where(hist < 0), color=COLORS['hist_neg'],
                alpha=0.5, width=0.8, label='Histogram (-)')

        ax4.set_ylabel('MACD', fontsize=10, color=COLORS['text'])
        ax4.set_title('MACD', fontsize=12, fontweight='bold',
                       color=COLORS['text'], pad=10)
        ax4.legend(loc='upper left', fontsize=8, facecolor=COLORS['panel'],
                   edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=0)

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        # 保存
        ensure_output_dir()
        filename = OUTPUT_DIR / f'{self.ticker}_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor=COLORS['bg'])
        print(f"  💾 チャート保存: {filename}")
        plt.close()

        return str(filename)

    def generate_report(self):
        """分析レポートを生成"""
        analysis = self.analyze_trend()

        report = f"""
{'═' * 60}
  {analysis['trend_emoji']} {self.ticker} 株価テクニカル分析レポート
{'═' * 60}

  📊 基本情報
  {'─' * 40}
  ティッカー     : {self.ticker}
  分析期間       : {self.period}
  最新終値       : ${analysis['latest_price']:.2f}
  期間最高値     : ${analysis['high']:.2f}
  期間最安値     : ${analysis['low']:.2f}
  期間リターン   : {analysis['period_return']:+.2f}%
  平均出来高     : {analysis['avg_volume']:,.0f}

  📈 移動平均線
  {'─' * 40}
  SMA 10日       : ${analysis['sma_10']:.2f}
  SMA 30日       : ${analysis['sma_30']:.2f}
  ボラティリティ : {analysis['volatility']:.2f}

  🔍 トレンド分析
  {'─' * 40}
  {analysis['trend']}

  🎯 RSI指標
  {'─' * 40}
  RSI値          : {analysis['rsi']:.2f}
  シグナル       : {analysis['rsi_signal']}

  📉 MACD
  {'─' * 40}
  MACD           : {analysis['macd']:.4f}
  シグナル線     : {analysis['signal']:.4f}
  判定           : {analysis['macd_signal']}

  📋 テクニカル指標の要約
  {'─' * 40}
  • SMA   : 短期(10)が長期(30)の上 → 上昇トレンド
  • RSI   : 70超=買われすぎ / 30未満=売られすぎ
  • MACD  : MACDがシグナル線を上抜け → 買いシグナル

  ⚠️  免責事項
  {'─' * 40}
  この分析は教育目的であり、投資助言ではありません。
  実際の投資決定は自己責任で行ってください。
  過去のパフォーマンスが将来の結果を保証するものではありません。

{'═' * 60}
  生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'═' * 60}
"""

        # レポートを保存
        ensure_output_dir()
        filename = OUTPUT_DIR / f'{self.ticker}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"  📝 レポート保存: {filename}")
        print(report)

        return str(filename)

    def run(self):
        """分析を実行"""
        print(f"\n{'━' * 60}")
        print(f"  📊 株価テクニカル分析 ─ {self.ticker}")
        print(f"  📅 期間: {self.period}")
        print(f"{'━' * 60}\n")

        # API制限対応: タイムアウト設定
        time.sleep(3)

        # データ取得
        if not self.fetch_data():
            return False

        # API制限対応
        time.sleep(2)

        # テクニカル指標計算
        self.calculate_technical_indicators()

        # API制限対応
        time.sleep(2)

        # グラフ生成
        chart_file = self.plot_chart()

        # レポート生成
        report_file = self.generate_report()

        print(f"\n{'━' * 60}")
        print(f"  ✅ 分析完了！")
        print(f"  📊 チャート : {chart_file}")
        print(f"  📝 レポート : {report_file}")
        print(f"{'━' * 60}\n")

        return True


def compare_stocks(tickers, period='1mo'):
    """複数銘柄の比較チャートを生成"""
    print(f"\n{'━' * 60}")
    print(f"  📊 複数銘柄比較分析")
    print(f"  📅 銘柄: {', '.join(tickers)} | 期間: {period}")
    print(f"{'━' * 60}\n")

    all_data = {}

    for ticker in tickers:
        print(f"  ⏳ {ticker} のデータを取得中...")
        time.sleep(3)
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            if not data.empty:
                all_data[ticker] = data
                print(f"  ✅ {ticker}: {len(data)}件取得")
            else:
                print(f"  ❌ {ticker}: データなし")
        except Exception as e:
            print(f"  ❌ {ticker}: エラー - {e}")

    if len(all_data) < 2:
        print("  ❌ 比較には2銘柄以上のデータが必要です")
        return False

    # ─── 比較チャート描画 ────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.patch.set_facecolor(COLORS['bg'])
    fig.suptitle('複数銘柄比較分析', fontsize=20, fontweight='bold',
                 color=COLORS['text'], y=0.995)
    fig.text(0.5, 0.97, f'{" vs ".join(tickers)}  |  期間: {period}',
             ha='center', fontsize=12, color=COLORS['accent'], alpha=0.85)

    chart_colors = ['#00d4ff', '#ff6b6b', '#ffd93d', '#6bcb77', '#c084fc', '#fb923c']

    for ax in axes.flat:
        ax.set_facecolor(COLORS['panel'])
        ax.tick_params(colors=COLORS['text'], labelsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['grid'])
        ax.spines['left'].set_color(COLORS['grid'])
        ax.grid(True, alpha=0.15, color=COLORS['grid'], linestyle='--')

    # (1) 正規化価格比較
    ax1 = axes[0, 0]
    for i, (ticker, data) in enumerate(all_data.items()):
        normalized = (data['Close'] / data['Close'].iloc[0]) * 100
        ax1.plot(data.index, normalized, label=ticker,
                 color=chart_colors[i % len(chart_colors)], linewidth=2)
    ax1.set_title('正規化価格 (初日=100)', fontsize=12, fontweight='bold',
                   color=COLORS['text'], pad=10)
    ax1.set_ylabel('正規化価格', color=COLORS['text'])
    ax1.legend(facecolor=COLORS['panel'], edgecolor=COLORS['grid'],
               labelcolor=COLORS['text'])
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # (2) RSI比較
    ax2 = axes[0, 1]
    for i, (ticker, data) in enumerate(all_data.items()):
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        ax2.plot(data.index, rsi, label=ticker,
                 color=chart_colors[i % len(chart_colors)], linewidth=1.5)
    ax2.axhline(y=70, color=COLORS['overbought'], linestyle='--', alpha=0.5)
    ax2.axhline(y=30, color=COLORS['oversold'], linestyle='--', alpha=0.5)
    ax2.axhspan(70, 100, alpha=0.05, color=COLORS['overbought'])
    ax2.axhspan(0, 30, alpha=0.05, color=COLORS['oversold'])
    ax2.set_title('RSI 比較', fontsize=12, fontweight='bold',
                   color=COLORS['text'], pad=10)
    ax2.set_ylabel('RSI', color=COLORS['text'])
    ax2.set_ylim([0, 100])
    ax2.legend(facecolor=COLORS['panel'], edgecolor=COLORS['grid'],
               labelcolor=COLORS['text'])
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # (3) 日次リターン比較
    ax3 = axes[1, 0]
    for i, (ticker, data) in enumerate(all_data.items()):
        returns = data['Close'].pct_change() * 100
        ax3.plot(data.index, returns, label=ticker,
                 color=chart_colors[i % len(chart_colors)], linewidth=1, alpha=0.8)
    ax3.axhline(y=0, color=COLORS['text'], linestyle='-', alpha=0.3)
    ax3.set_title('日次リターン (%)', fontsize=12, fontweight='bold',
                   color=COLORS['text'], pad=10)
    ax3.set_ylabel('リターン (%)', color=COLORS['text'])
    ax3.legend(facecolor=COLORS['panel'], edgecolor=COLORS['grid'],
               labelcolor=COLORS['text'])
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # (4) 累積リターン比較
    ax4 = axes[1, 1]
    for i, (ticker, data) in enumerate(all_data.items()):
        cumulative = ((data['Close'] / data['Close'].iloc[0]) - 1) * 100
        ax4.plot(data.index, cumulative, label=ticker,
                 color=chart_colors[i % len(chart_colors)], linewidth=2)
        # 最終値をアノテーション
        ax4.annotate(f'{cumulative.iloc[-1]:+.1f}%',
                     xy=(data.index[-1], cumulative.iloc[-1]),
                     xytext=(5, 5 + i * 12), textcoords='offset points',
                     fontsize=9, color=chart_colors[i % len(chart_colors)],
                     fontweight='bold')
    ax4.axhline(y=0, color=COLORS['text'], linestyle='-', alpha=0.3)
    ax4.set_title('累積リターン (%)', fontsize=12, fontweight='bold',
                   color=COLORS['text'], pad=10)
    ax4.set_ylabel('累積リターン (%)', color=COLORS['text'])
    ax4.legend(facecolor=COLORS['panel'], edgecolor=COLORS['grid'],
               labelcolor=COLORS['text'])
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    ensure_output_dir()
    filename = OUTPUT_DIR / f'compare_{"_".join(tickers)}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close()

    print(f"\n  💾 比較チャート保存: {filename}")

    # ─── 比較サマリー ────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  📊 比較サマリー")
    print(f"{'═' * 60}")
    print(f"  {'銘柄':<8} {'最新価格':>12} {'期間リターン':>12} {'RSI':>8}")
    print(f"  {'─' * 44}")
    for ticker, data in all_data.items():
        latest = data['Close'].iloc[-1]
        ret = ((latest / data['Close'].iloc[0]) - 1) * 100
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        print(f"  {ticker:<8} ${latest:>10.2f} {ret:>+10.2f}% {rsi:>8.1f}")
    print(f"{'═' * 60}\n")

    return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='📊 株価テクニカル分析ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s AAPL 1mo          # Apple 1ヶ月分析
  %(prog)s TSLA 3mo          # Tesla 3ヶ月分析
  %(prog)s AAPL,TSLA,GOOGL 3mo  # 複数銘柄比較

有効な期間:
  1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
"""
    )
    parser.add_argument('ticker', nargs='?', default='AAPL',
                        help='ティッカーシンボル (例: AAPL, TSLA, GOOGL) カンマ区切りで複数指定可')
    parser.add_argument('period', nargs='?', default='1mo',
                        help='期間 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)')

    args = parser.parse_args()

    # カンマ区切りの場合は比較モード
    tickers = [t.strip().upper() for t in args.ticker.split(',')]

    if len(tickers) > 1:
        compare_stocks(tickers, args.period)
    else:
        analyzer = StockAnalyzer(tickers[0], args.period)
        analyzer.run()


if __name__ == "__main__":
    main()
