import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import requests

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Konrad's Monitor", page_icon="₿", layout="wide")

st.title("₿ konrads.ai — Bitcoin & MSTR Monitor")
st.markdown("**BTC Technicals • MSTR • Vergleich**")

# --- Grok AI Analysis ---
grok_analysis = """
**🧠 Grok AI Analysis – 03. Juni 2026**

- Bitcoin notiert weiter unter 70k in der Korrektur.
- Death Cross (EMA50 unter EMA200) bleibt aktiv.
- MSTR als leveraged BTC-Play zeigt höhere Volatilität.
- Langfristig: Geduld und schrittweises Nachkaufen (DCA).
"""

def calculate_ema(prices, period):
    if len(prices) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = (p * multiplier) + (ema * (1 - multiplier))
    return round(ema, 2)

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = pd.Series(prices).diff()
    gain = deltas.where(deltas > 0, 0)
    loss = -deltas.where(deltas < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else None

def get_data():
    try:
        # BTC
        cg = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
            timeout=15
        ).json()
        btc_price = float(cg["bitcoin"]["usd"])
        btc_change = float(cg["bitcoin"].get("usd_24h_change", 0))

        # MSTR
        mstr = yf.Ticker("MSTR")
        mstr_hist = mstr.history(period="5d")
        mstr_price = float(mstr_hist['Close'].iloc[-1])
        mstr_change = (mstr_price - float(mstr_hist['Close'].iloc[-2])) / float(mstr_hist['Close'].iloc[-2]) * 100

        # Historische BTC
        hist = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": "365", "interval": "daily"},
            timeout=20
        ).json()
        raw_prices = [p[1] for p in hist["prices"]]

        ema50 = calculate_ema(raw_prices, 50)
        ema200 = calculate_ema(raw_prices, 200)
        rsi14 = calculate_rsi(raw_prices, 14)

        df_btc = pd.DataFrame({"BTC": raw_prices})
        df_btc["EMA_50"] = [calculate_ema(raw_prices[:i+1], 50) if i >= 49 else None for i in range(len(raw_prices))]
        df_btc["EMA_200"] = [calculate_ema(raw_prices[:i+1], 200) if i >= 199 else None for i in range(len(raw_prices))]

        # MSTR lange Historie
        mstr_long = yf.download("MSTR", period="1y", interval="1d", progress=False)['Close']

        return btc_price, btc_change, mstr_price, mstr_change, ema50, ema200, rsi14, df_btc, mstr_long

    except Exception as e:
        st.error(f"Verbindungsfehler: {str(e)[:80]}...")
        return None, None, None, None, None, None, None, None, None


# --- Dashboard ---
placeholder = st.empty()

while True:
    data = get_data()
    
    with placeholder.container():
        if data[0] is None:
            st.warning("🔄 Lade Daten...")
        else:
            btc, btc_chg, mstr, mstr_chg, ema50, ema200, rsi14, df_btc, mstr_long = data

            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1.8])
            
            with col1:
                st.metric("**Bitcoin (BTC)**", f"${btc:,.2f}", f"{btc_chg:+.2f}%")
            
            with col2:
                st.metric("**MicroStrategy (MSTR)**", f"${mstr:,.2f}", f"{mstr_chg:+.2f}%")
            
            with col3:
                if ema50:
                    st.metric("**EMA 50**", f"${ema50:,.2f}", f"{(btc - ema50)/ema50*100:+.2f}%")
            
            with col4:
                if ema200:
                    st.metric("**EMA 200**", f"${ema200:,.2f}", f"{(btc - ema200)/ema200*100:+.2f}%")
            
            with col5:
                status = "🟢 Bullish" if ema200 and btc > ema200 else "🔴 Bearish"
                if status == "🟢 Bullish":
                    st.success(f"**{status}**")
                else:
                    st.error(f"**{status}**")

            st.subheader("Bitcoin Kurs + EMAs - Letzte 12 Monate")
            st.line_chart(df_btc[["BTC", "EMA_50", "EMA_200"]], width='stretch', height=420)

            # BTC vs MSTR Vergleich - Einfach und robust
            st.subheader("BTC vs MSTR Performance (normiert auf 100 seit 1 Jahr)")
            compare = pd.DataFrame()
            compare["BTC"] = df_btc["BTC"] / df_btc["BTC"].iloc[0] * 100

            if len(mstr_long) > 0:
                compare["MSTR"] = mstr_long / mstr_long.iloc[0] * 100

            st.line_chart(compare, width='stretch', height=480)

            st.subheader("My daily AI Analysis")
            st.markdown(grok_analysis)

            st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')} • konrads.ai")

    time.sleep(90)
