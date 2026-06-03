import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import yfinance as yf

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="konrads.ai", page_icon="₿", layout="wide")

st.title("konrads.ai — Bitcoin Monitor")

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

try:
    # BTC Daten
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

    df_btc = pd.DataFrame({"BTC": raw_prices})
    df_btc["EMA_50"] = [calculate_ema(raw_prices[:i+1], 50) if i >= 49 else None for i in range(len(raw_prices))]
    df_btc["EMA_200"] = [calculate_ema(raw_prices[:i+1], 200) if i >= 199 else None for i in range(len(raw_prices))]

    # Metriken
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
    st.line_chart(df_btc[["BTC", "EMA_50", "EMA_200"]], width='stretch', height=500)

    # MSTR nur als Preis
    try:
        mstr = yf.Ticker("MSTR")
        mstr_hist = mstr.history(period="5d")
        mstr_price = float(mstr_hist['Close'].iloc[-1])
        mstr_change = (mstr_price - float(mstr_hist['Close'].iloc[-2])) / float(mstr_hist['Close'].iloc[-2]) * 100
        st.metric("**MicroStrategy (MSTR)**", f"${mstr_price:,.2f}", f"{mstr_change:+.2f}%")
    except:
        pass

except Exception as e:
    st.error(f"Fehler beim Laden: {str(e)[:100]}...")

st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')} • konrads.ai")
