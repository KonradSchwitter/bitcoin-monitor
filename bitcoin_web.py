import streamlit as st
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="konrads.ai", page_icon="₿", layout="wide")

st.title("konrads.ai — Live Monitor")

tab1, tab2 = st.tabs(["Bitcoin Monitor", "MSTR Monitor"])

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

# ====================== TAB 1: BITCOIN ======================
with tab1:
    st.subheader("Bitcoin Monitor")
    try:
        cg = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
            timeout=15
        ).json()
        btc_price = float(cg["bitcoin"]["usd"])
        btc_change = float(cg["bitcoin"].get("usd_24h_change", 0))

        hist = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": "365", "interval": "daily"},
            timeout=20
        ).json()
        raw_prices = [p[1] for p in hist["prices"]]

        ema50 = calculate_ema(raw_prices, 50)
        ema200 = calculate_ema(raw_prices, 200)

        df = pd.DataFrame({"BTC": raw_prices})
        df["EMA_50"] = [calculate_ema(raw_prices[:i+1], 50) if i >= 49 else None for i in range(len(raw_prices))]
        df["EMA_200"] = [calculate_ema(raw_prices[:i+1], 200) if i >= 199 else None for i in range(len(raw_prices))]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("**Bitcoin Preis**", f"${btc_price:,.2f}", f"{btc_change:+.2f}%")
        with col2:
            st.metric("**EMA 50**", f"${ema50:,.2f}" if ema50 else "—")
        with col3:
            st.metric("**EMA 200**", f"${ema200:,.2f}" if ema200 else "—")

        st.line_chart(df[["BTC", "EMA_50", "EMA_200"]], width='stretch', height=500)

    except:
        st.error("Fehler beim Laden der Bitcoin-Daten")

# ====================== TAB 2: MSTR ======================
with tab2:
    st.subheader("MSTR Monitor")
    try:
        mstr = yf.Ticker("MSTR")
        mstr_hist = mstr.history(period="5d")
        mstr_price = float(mstr_hist['Close'].iloc[-1])
        mstr_change = (mstr_price - float(mstr_hist['Close'].iloc[-2])) / float(mstr_hist['Close'].iloc[-2]) * 100

        # Lange Historie für MSTR
        mstr_long = yf.download("MSTR", period="1y", interval="1d", progress=False)['Close']
        mstr_raw = list(mstr_long)

        ema50_mstr = calculate_ema(mstr_raw, 50)
        ema200_mstr = calculate_ema(mstr_raw, 200)

        df_mstr = pd.DataFrame({"MSTR": mstr_raw})
        df_mstr["EMA_50"] = [calculate_ema(mstr_raw[:i+1], 50) if i >= 49 else None for i in range(len(mstr_raw))]
        df_mstr["EMA_200"] = [calculate_ema(mstr_raw[:i+1], 200) if i >= 199 else None for i in range(len(mstr_raw))]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("**MSTR Preis**", f"${mstr_price:,.2f}", f"{mstr_change:+.2f}%")
        with col2:
            st.metric("**EMA 50**", f"${ema50_mstr:,.2f}" if ema50_mstr else "—")
        with col3:
            st.metric("**EMA 200**", f"${ema200_mstr:,.2f}" if ema200_mstr else "—")

        st.line_chart(df_mstr[["MSTR", "EMA_50", "EMA_200"]], width='stretch', height=500)

    except Exception as e:
        st.error(f"Fehler beim Laden der MSTR-Daten: {str(e)[:100]}")

st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')} • konrads.ai")
