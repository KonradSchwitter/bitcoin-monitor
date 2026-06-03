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

def get_btc_data():
    try:
        cg = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
            timeout=15
        ).json()
        price = float(cg["bitcoin"]["usd"])
        change = float(cg["bitcoin"].get("usd_24h_change", 0))

        hist = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": "365", "interval": "daily"},
            timeout=20
        ).json()
        prices = [p[1] for p in hist["prices"]]

        ema50 = calculate_ema(prices, 50)
        ema200 = calculate_ema(prices, 200)

        df = pd.DataFrame({"BTC": prices})
        df["EMA_50"] = [calculate_ema(prices[:i+1], 50) if i >= 49 else None for i in range(len(prices))]
        df["EMA_200"] = [calculate_ema(prices[:i+1], 200) if i >= 199 else None for i in range(len(prices))]

        return price, change, ema50, ema200, df
    except:
        return None, None, None, None, None

def get_mstr_data():
    try:
        mstr = yf.Ticker("MSTR")
        mstr_hist = mstr.history(period="5d")
        price = float(mstr_hist['Close'].iloc[-1])
        change = (price - float(mstr_hist['Close'].iloc[-2])) / float(mstr_hist['Close'].iloc[-2]) * 100

        mstr_long = yf.download("MSTR", period="1y", interval="1d", progress=False)['Close']
        mstr_raw = list(mstr_long)

        ema50 = calculate_ema(mstr_raw, 50)
        ema200 = calculate_ema(mstr_raw, 200)

        df = pd.DataFrame({"MSTR": mstr_raw})
        df["EMA_50"] = [calculate_ema(mstr_raw[:i+1], 50) if i >= 49 else None for i in range(len(mstr_raw))]
        df["EMA_200"] = [calculate_ema(mstr_raw[:i+1], 200) if i >= 199 else None for i in range(len(mstr_raw))]

        return price, change, ema50, ema200, df
    except:
        return None, None, None, None, None


# --- Dashboard ---
placeholder = st.empty()

while True:
    btc_price, btc_change, btc_ema50, btc_ema200, df_btc = get_btc_data()
    mstr_price, mstr_change, mstr_ema50, mstr_ema200, df_mstr = get_mstr_data()
    
    with placeholder.container():
        # Metriken
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("**Bitcoin**", f"${btc_price:,.2f}" if btc_price else "—", f"{btc_change:+.2f}%" if btc_change else "")
        with col2:
            st.metric("**MSTR**", f"${mstr_price:,.2f}" if mstr_price else "—", f"{mstr_change:+.2f}%" if mstr_change else "")
        with col3:
            st.metric("**BTC EMA 200**", f"${btc_ema200:,.2f}" if btc_ema200 else "—")
        with col4:
            st.metric("**MSTR EMA 200**", f"${mstr_ema200:,.2f}" if mstr_ema200 else "—")

        # BTC Chart
        st.subheader("Bitcoin Kurs + EMAs - Letzte 12 Monate")
        if df_btc is not None:
            st.line_chart(df_btc[["BTC", "EMA_50", "EMA_200"]], width='stretch', height=400)
        else:
            st.warning("BTC Chart konnte nicht geladen werden")

        # MSTR Chart
        st.subheader("MSTR Kurs + EMAs - Letzte 12 Monate")
        if df_mstr is not None and len(df_mstr) > 0:
            st.line_chart(df_mstr[["MSTR", "EMA_50", "EMA_200"]], width='stretch', height=400)
        else:
            st.warning("MSTR Chart konnte nicht geladen werden")

        st.subheader("My daily AI Analysis")
        st.markdown(grok_analysis)

        st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')} • konrads.ai")

    time.sleep(90)
