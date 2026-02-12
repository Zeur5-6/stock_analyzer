"""
Stock Technical Analyzer - Streamlit Web UI
株価テクニカル分析 Web ダッシュボード

起動方法:
    streamlit run app.py
"""

import time
from datetime import datetime

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ─── ページ設定 ─────────────────────────────────────────
st.set_page_config(
    page_title="📊 Stock Technical Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── カラーパレット ─────────────────────────────────────
COLORS = {
    'bg':         '#0e1117',
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

CHART_COLORS = ['#00d4ff', '#ff6b6b', '#ffd93d', '#6bcb77', '#c084fc', '#fb923c']

# 日本語フォント
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'Segoe UI Symbol']
plt.rcParams['axes.unicode_minus'] = False

# ─── カスタム CSS ──────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp { font-family: 'Inter', sans-serif; }

    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 212, 255, 0.15);
    }
    .metric-label {
        font-size: 13px;
        color: #8899aa;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #e0e0e0;
    }
    .metric-delta-up { color: #00c853; font-size: 14px; font-weight: 600; }
    .metric-delta-down { color: #ff1744; font-size: 14px; font-weight: 600; }

    .trend-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
    }
    .trend-bullish { background: rgba(0, 200, 83, 0.15); color: #00c853; border: 1px solid rgba(0, 200, 83, 0.3); }
    .trend-bearish { background: rgba(255, 23, 68, 0.15); color: #ff1744; border: 1px solid rgba(255, 23, 68, 0.3); }
    .trend-neutral { background: rgba(255, 217, 61, 0.15); color: #ffd93d; border: 1px solid rgba(255, 217, 61, 0.3); }

    .header-title {
        background: linear-gradient(135deg, #00d4ff, #6bcb77);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 32px;
        font-weight: 700;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1117 0%, #16213e 100%);
    }
</style>
""", unsafe_allow_html=True)


# ─── データ取得 ─────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_stock_data(ticker, period):
    """Yahoo Financeからデータ取得（5分キャッシュ）"""
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data


def calculate_indicators(data):
    """テクニカル指標を計算"""
    df = data.copy()

    # SMA
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_30'] = df['Close'].rolling(window=30).mean()
    df['SMA_60'] = df['Close'].rolling(window=60).mean()

    # ボラティリティ
    df['Volatility'] = df['Close'].rolling(window=20).std()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']

    # ボリンジャーバンド
    bb_period = 20
    df['BB_Middle'] = df['Close'].rolling(window=bb_period).mean()
    bb_std = df['Close'].rolling(window=bb_period).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)

    return df


def style_axis(ax):
    """軸のダークテーマスタイリング"""
    ax.set_facecolor(COLORS['panel'])
    ax.tick_params(colors=COLORS['text'], labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(COLORS['grid'])
    ax.spines['left'].set_color(COLORS['grid'])
    ax.grid(True, alpha=0.15, color=COLORS['grid'], linestyle='--')


def create_single_chart(data, ticker):
    """単一銘柄のチャート生成"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 14),
                             gridspec_kw={'height_ratios': [3, 1, 1.5, 1.5]})
    fig.patch.set_facecolor(COLORS['bg'])
    for ax in axes:
        style_axis(ax)

    # 価格チャート
    ax1 = axes[0]
    ax1.plot(data.index, data['Close'], label='終値', color=COLORS['price'], linewidth=2)
    ax1.plot(data.index, data['SMA_10'], label='SMA 10', color=COLORS['sma10'], alpha=0.8, linewidth=1.2)
    ax1.plot(data.index, data['SMA_30'], label='SMA 30', color=COLORS['sma30'], alpha=0.8, linewidth=1.2)
    ax1.fill_between(data.index, data['BB_Upper'], data['BB_Lower'],
                     alpha=0.08, color=COLORS['bb_fill'], label='Bollinger Bands')
    ax1.plot(data.index, data['BB_Upper'], color=COLORS['bb_fill'], alpha=0.3, linewidth=0.8, linestyle='--')
    ax1.plot(data.index, data['BB_Lower'], color=COLORS['bb_fill'], alpha=0.3, linewidth=0.8, linestyle='--')
    ax1.set_ylabel('価格 (USD)', color=COLORS['text'])
    ax1.set_title('価格・移動平均線・ボリンジャーバンド', fontsize=12, fontweight='bold', color=COLORS['text'], pad=10)
    ax1.legend(loc='upper left', fontsize=8, facecolor=COLORS['panel'], edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # 出来高
    ax2 = axes[1]
    vol_colors = [COLORS['vol_up'] if data['Close'].iloc[i] >= data['Open'].iloc[i]
                  else COLORS['vol_down'] for i in range(len(data))]
    ax2.bar(data.index, data['Volume'], color=vol_colors, alpha=0.7, width=0.8)
    ax2.set_ylabel('出来高', color=COLORS['text'])
    ax2.set_title('出来高 (Volume)', fontsize=12, fontweight='bold', color=COLORS['text'], pad=10)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.0f}M'))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # RSI
    ax3 = axes[2]
    ax3.plot(data.index, data['RSI'], color=COLORS['rsi'], linewidth=1.5)
    ax3.axhline(y=70, color=COLORS['overbought'], linestyle='--', alpha=0.6)
    ax3.axhline(y=30, color=COLORS['oversold'], linestyle='--', alpha=0.6)
    ax3.axhspan(70, 100, alpha=0.05, color=COLORS['overbought'])
    ax3.axhspan(0, 30, alpha=0.05, color=COLORS['oversold'])
    ax3.set_ylabel('RSI', color=COLORS['text'])
    ax3.set_title('相対力指数 (RSI)', fontsize=12, fontweight='bold', color=COLORS['text'], pad=10)
    ax3.set_ylim([0, 100])
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # MACD
    ax4 = axes[3]
    ax4.plot(data.index, data['MACD'], label='MACD', color=COLORS['macd'], linewidth=1.5)
    ax4.plot(data.index, data['Signal'], label='Signal', color=COLORS['signal'], linewidth=1.5)
    hist = data['Histogram']
    ax4.bar(data.index, hist.where(hist >= 0), color=COLORS['hist_pos'], alpha=0.5, width=0.8)
    ax4.bar(data.index, hist.where(hist < 0), color=COLORS['hist_neg'], alpha=0.5, width=0.8)
    ax4.set_ylabel('MACD', color=COLORS['text'])
    ax4.set_title('MACD', fontsize=12, fontweight='bold', color=COLORS['text'], pad=10)
    ax4.legend(loc='upper left', fontsize=8, facecolor=COLORS['panel'], edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    plt.tight_layout()
    return fig


def create_comparison_chart(all_data, tickers):
    """複数銘柄の比較チャート生成"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.patch.set_facecolor(COLORS['bg'])
    for ax in axes.flat:
        style_axis(ax)

    # 正規化価格
    ax1 = axes[0, 0]
    for i, (ticker, data) in enumerate(all_data.items()):
        norm = (data['Close'] / data['Close'].iloc[0]) * 100
        ax1.plot(data.index, norm, label=ticker, color=CHART_COLORS[i % len(CHART_COLORS)], linewidth=2)
    ax1.set_title('正規化価格 (初日=100)', fontsize=12, fontweight='bold', color=COLORS['text'])
    ax1.legend(facecolor=COLORS['panel'], edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # RSI比較
    ax2 = axes[0, 1]
    for i, (ticker, data) in enumerate(all_data.items()):
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        ax2.plot(data.index, rsi, label=ticker, color=CHART_COLORS[i % len(CHART_COLORS)], linewidth=1.5)
    ax2.axhline(70, color=COLORS['overbought'], linestyle='--', alpha=0.5)
    ax2.axhline(30, color=COLORS['oversold'], linestyle='--', alpha=0.5)
    ax2.set_title('RSI 比較', fontsize=12, fontweight='bold', color=COLORS['text'])
    ax2.set_ylim([0, 100])
    ax2.legend(facecolor=COLORS['panel'], edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # 日次リターン
    ax3 = axes[1, 0]
    for i, (ticker, data) in enumerate(all_data.items()):
        ret = data['Close'].pct_change() * 100
        ax3.plot(data.index, ret, label=ticker, color=CHART_COLORS[i % len(CHART_COLORS)], linewidth=1, alpha=0.8)
    ax3.axhline(0, color=COLORS['text'], linestyle='-', alpha=0.3)
    ax3.set_title('日次リターン (%)', fontsize=12, fontweight='bold', color=COLORS['text'])
    ax3.legend(facecolor=COLORS['panel'], edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    # 累積リターン
    ax4 = axes[1, 1]
    for i, (ticker, data) in enumerate(all_data.items()):
        cum = ((data['Close'] / data['Close'].iloc[0]) - 1) * 100
        ax4.plot(data.index, cum, label=ticker, color=CHART_COLORS[i % len(CHART_COLORS)], linewidth=2)
        ax4.annotate(f'{cum.iloc[-1]:+.1f}%', xy=(data.index[-1], cum.iloc[-1]),
                     fontsize=9, color=CHART_COLORS[i % len(CHART_COLORS)], fontweight='bold')
    ax4.axhline(0, color=COLORS['text'], linestyle='-', alpha=0.3)
    ax4.set_title('累積リターン (%)', fontsize=12, fontweight='bold', color=COLORS['text'])
    ax4.legend(facecolor=COLORS['panel'], edgecolor=COLORS['grid'], labelcolor=COLORS['text'])
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════
#  サイドバー
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ 分析設定")
    st.markdown("---")

    mode = st.radio("📋 分析モード", ["単一銘柄分析", "複数銘柄比較"],
                    help="単一銘柄の詳細分析、または複数銘柄の比較を選択")

    if mode == "単一銘柄分析":
        ticker_input = st.text_input("🏷️ ティッカーシンボル", value="AAPL",
                                     help="例: AAPL, TSLA, GOOGL, MSFT")
    else:
        ticker_input = st.text_input("🏷️ ティッカーシンボル（カンマ区切り）",
                                     value="AAPL, TSLA, GOOGL",
                                     help="例: AAPL, TSLA, GOOGL")

    period = st.selectbox("📅 分析期間", [
        ("1日", "1d"), ("5日", "5d"), ("1ヶ月", "1mo"),
        ("3ヶ月", "3mo"), ("6ヶ月", "6mo"), ("1年", "1y"),
        ("2年", "2y"), ("5年", "5y"), ("最大", "max")
    ], index=2, format_func=lambda x: x[0])

    st.markdown("---")
    analyze_btn = st.button("🚀 分析開始", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; opacity:0.5; font-size:12px;">
        ⚠️ 教育目的のみ<br>投資助言ではありません
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  メインコンテンツ
# ═══════════════════════════════════════════════════════════
st.markdown('<h1 class="header-title">📊 Stock Technical Analyzer</h1>', unsafe_allow_html=True)
st.markdown("*株価テクニカル分析ダッシュボード — Yahoo Finance データ使用*")
st.markdown("---")

if analyze_btn:
    tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]

    if not tickers:
        st.error("❌ ティッカーシンボルを入力してください")
        st.stop()

    selected_period = period[1]

    if mode == "単一銘柄分析":
        # ─── 単一銘柄分析 ────────────────────────────────
        ticker = tickers[0]

        with st.spinner(f"⏳ {ticker} のデータを取得中..."):
            try:
                data = fetch_stock_data(ticker, selected_period)
            except Exception as e:
                st.error(f"❌ データ取得エラー: {e}")
                st.stop()

        if data.empty:
            st.error(f"❌ {ticker} のデータが見つかりません")
            st.stop()

        data = calculate_indicators(data)

        # 分析データ
        latest = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2] if len(data) > 1 else latest
        change = latest - prev
        change_pct = (change / prev) * 100
        period_return = ((latest / data['Close'].iloc[0]) - 1) * 100
        rsi = data['RSI'].iloc[-1] if not pd.isna(data['RSI'].iloc[-1]) else 0
        macd_val = data['MACD'].iloc[-1] if not pd.isna(data['MACD'].iloc[-1]) else 0
        signal_val = data['Signal'].iloc[-1] if not pd.isna(data['Signal'].iloc[-1]) else 0

        # トレンド判定
        sma10 = data['SMA_10'].iloc[-1]
        sma30 = data['SMA_30'].iloc[-1]
        if not pd.isna(sma10) and not pd.isna(sma30):
            if latest > sma10 > sma30:
                trend_text, trend_class = "📈 強い上昇トレンド", "trend-bullish"
            elif latest > sma10:
                trend_text, trend_class = "📊 上昇トレンド", "trend-bullish"
            elif latest < sma10 < sma30:
                trend_text, trend_class = "📉 強い下降トレンド", "trend-bearish"
            elif latest < sma10:
                trend_text, trend_class = "📉 下降トレンド", "trend-bearish"
            else:
                trend_text, trend_class = "➡️ 横ばい", "trend-neutral"
        else:
            trend_text, trend_class = "📊 データ不足", "trend-neutral"

        # ─── メトリクスカード ────────────────────────────
        st.markdown(f"### {ticker} — テクニカル分析")
        delta_cls = "metric-delta-up" if change >= 0 else "metric-delta-down"
        delta_sym = "▲" if change >= 0 else "▼"

        cols = st.columns(5)
        metrics = [
            ("最新価格", f"${latest:.2f}", f"{delta_sym} {abs(change):.2f} ({change_pct:+.2f}%)"),
            ("期間リターン", f"{period_return:+.2f}%", None),
            ("RSI", f"{rsi:.1f}", "買われすぎ" if rsi > 70 else ("売られすぎ" if rsi < 30 else "中立")),
            ("MACD", f"{macd_val:.4f}", "買い" if macd_val > signal_val else "売り"),
            ("出来高 (平均)", f"{data['Volume'].mean()/1e6:.1f}M", None),
        ]

        for i, (label, value, delta) in enumerate(metrics):
            with cols[i]:
                delta_html = ""
                if delta:
                    delta_html = f'<div class="{delta_cls}">{delta}</div>'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    {delta_html}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")

        # トレンドバッジ
        st.markdown(f'<span class="trend-badge {trend_class}">{trend_text}</span>',
                    unsafe_allow_html=True)
        st.markdown("")

        # チャート
        fig = create_single_chart(data, ticker)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # データテーブル
        with st.expander("📋 直近のデータを表示"):
            display_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_30', 'RSI', 'MACD']
            available = [c for c in display_cols if c in data.columns]
            st.dataframe(data[available].tail(20).style.format({
                'Open': '${:.2f}', 'High': '${:.2f}', 'Low': '${:.2f}', 'Close': '${:.2f}',
                'Volume': '{:,.0f}', 'SMA_10': '${:.2f}', 'SMA_30': '${:.2f}',
                'RSI': '{:.2f}', 'MACD': '{:.4f}'
            }), use_container_width=True)

    else:
        # ─── 複数銘柄比較 ─────────────────────────────────
        if len(tickers) < 2:
            st.warning("⚠️ 比較には2銘柄以上を入力してください（カンマ区切り）")
            st.stop()

        all_data = {}
        progress = st.progress(0, text="データを取得中...")

        for i, ticker in enumerate(tickers):
            progress.progress((i + 1) / len(tickers), text=f"⏳ {ticker} を取得中...")
            try:
                d = fetch_stock_data(ticker, selected_period)
                if not d.empty:
                    all_data[ticker] = d
            except Exception:
                st.warning(f"⚠️ {ticker} のデータ取得に失敗")

        progress.empty()

        if len(all_data) < 2:
            st.error("❌ 比較できる銘柄が不足しています")
            st.stop()

        # 比較サマリー
        st.markdown("### 📊 比較サマリー")
        cols = st.columns(len(all_data))
        for i, (ticker, d) in enumerate(all_data.items()):
            latest = d['Close'].iloc[-1]
            ret = ((latest / d['Close'].iloc[0]) - 1) * 100
            delta_cls = "metric-delta-up" if ret >= 0 else "metric-delta-down"
            with cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{ticker}</div>
                    <div class="metric-value">${latest:.2f}</div>
                    <div class="{delta_cls}">{ret:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")

        # 比較チャート
        fig = create_comparison_chart(all_data, tickers)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

else:
    # ─── ウェルカムスクリーン ──────────────────────────────
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 64px; margin-bottom: 16px;">📊</div>
        <h2 style="color: #e0e0e0;">分析を開始しましょう</h2>
        <p style="color: #8899aa; font-size: 16px; max-width: 500px; margin: 0 auto;">
            サイドバーからティッカーシンボルと期間を入力し、<br>
            <strong style="color: #00d4ff;">「🚀 分析開始」</strong> をクリックしてください
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 人気銘柄のクイックアクセス
    st.markdown("#### 💡 人気銘柄")
    pop_cols = st.columns(6)
    popular = [("AAPL", "Apple"), ("TSLA", "Tesla"), ("GOOGL", "Google"),
               ("MSFT", "Microsoft"), ("AMZN", "Amazon"), ("NVDA", "NVIDIA")]
    for i, (sym, name) in enumerate(popular):
        with pop_cols[i]:
            st.markdown(f"""
            <div class="metric-card" style="cursor: pointer;">
                <div class="metric-label">{name}</div>
                <div class="metric-value" style="font-size: 20px;">{sym}</div>
            </div>
            """, unsafe_allow_html=True)
