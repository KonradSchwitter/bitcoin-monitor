import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="konrads.ai", page_icon="₿", layout="wide")

st.title("konrads.ai — Live Monitor")

tab1, tab2 = st.tabs(["Bitcoin Monitor", "MSTR Monitor"])

def calculate_ema(prices, period):
    prices = [p for p in prices if pd.notna(p)]
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
        # Aktueller Preis
        btc = yf.Ticker("BTC-USD")
        btc_hist = btc.history(period="5d")
        btc_price = float(btc_hist['Close'].iloc[-1])
        btc_change = (btc_price - float(btc_hist['Close'].iloc[-2])) / float(btc_hist['Close'].iloc[-2]) * 100

        # Historische Daten
        btc_long = yf.download("BTC-USD", period="1y", interval="1d", progress=False, auto_adjust=True)
        raw_prices = btc_long['Close'].dropna().tolist()   # ← hier war der Fehler

        st.caption(f"Historische Datenpunkte BTC: {len(raw_prices)}")

        ema50 = calculate_ema(raw_prices, 50)
        ema200 = calculate_ema(raw_prices, 200)

        df = pd.DataFrame({"Price": raw_prices})
        df["EMA_50"] = [calculate_ema(raw_prices[:i+1], 50) if i >= 49 else None for i in range(len(raw_prices))]
        df["EMA_200"] = [calculate_ema(raw_prices[:i+1], 200) if i >= 199 else None for i in range(len(raw_prices))]

        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        with col1:
            st.metric("**Bitcoin Preis**", f"${btc_price:,.2f}", f"{btc_change:+.2f}%")
        with col2:
            st.metric("**EMA 50**", f"${ema50:,.2f}" if ema50 else "—")
        with col3:
            st.metric("**EMA 200**", f"${ema200:,.2f}" if ema200 else "—")
        with col4:
            status = "🟢 Bullish" if ema200 and btc_price > ema200 else "🔴 Bearish"
            if status == "🟢 Bullish":
                st.success(f"**{status}**")
            else:
                st.error(f"**{status}**")

        st.subheader("Bitcoin Kurs + EMAs - Letzte 12 Monate")
        st.line_chart(df[["Price", "EMA_50", "EMA_200"]], width='stretch', height=520)

    except Exception as e:
        st.error(f"Fehler Bitcoin: {str(e)[:100]}")

# ====================== TAB 2: MSTR ======================
with tab2:
    st.subheader("MSTR Monitor")
    try:
        mstr = yf.Ticker("MSTR")
        mstr_hist = mstr.history(period="5d")
        mstr_price = float(mstr_hist['Close'].iloc[-1])
        mstr_change = (mstr_price - float(mstr_hist['Close'].iloc[-2])) / float(mstr_hist['Close'].iloc[-2]) * 100

        mstr_long = yf.download("MSTR", period="1y", interval="1d", progress=False, auto_adjust=True)
        raw_prices = mstr_long['Close'].dropna().tolist()

        st.caption(f"Historische Datenpunkte MSTR: {len(raw_prices)}")

        ema50 = calculate_ema(raw_prices, 50)
        ema200 = calculate_ema(raw_prices, 200)

        df = pd.DataFrame({"Price": raw_prices})
        df["EMA_50"] = [calculate_ema(raw_prices[:i+1], 50) if i >= 49 else None for i in range(len(raw_prices))]
        df["EMA_200"] = [calculate_ema(raw_prices[:i+1], 200) if i >= 199 else None for i in range(len(raw_prices))]

        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        with col1:
            st.metric("**MSTR Preis**", f"${mstr_price:,.2f}", f"{mstr_change:+.2f}%")
        with col2:
            st.metric("**EMA 50**", f"${ema50:,.2f}" if ema50 else "—")
        with col3:
            st.metric("**EMA 200**", f"${ema200:,.2f}" if ema200 else "—")
        with col4:
            status = "🟢 Bullish" if ema200 and mstr_price > ema200 else "🔴 Bearish"
            if status == "🟢 Bullish":
                st.success(f"**{status}**")
            else:
                st.error(f"**{status}**")

        st.subheader("MSTR Kurs + EMAs - Letzte 12 Monate")
        st.line_chart(df[["Price", "EMA_50", "EMA_200"]], width='stretch', height=520)

    except Exception as e:
        st.error(f"Fehler MSTR: {str(e)[:100]}")

st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')} • konrads.ai")
