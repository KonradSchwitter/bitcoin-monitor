import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Konrad's Monitor", page_icon="₿", layout="wide")

st.title("₿ konrads.ai — Bitcoin & MSTR Monitor")
st.markdown("**BTC Technicals • MSTR Technicals**")

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

@st.cache_data(ttl=300)
def get_historical_data():
    btc = yf.download("BTC-USD", period="1y", interval="1d", progress=False)['Close']
    mstr = yf.download("MSTR", period="1y", interval="1d", progress=False)['Close']
    return btc, mstr

def get_current_data():
    try:
        btc = yf.Ticker("BTC-USD").history(period="5d")
        btc_price = float(btc['Close'].iloc[-1])
        btc_change = (btc_price - float(btc['Close'].iloc[-2])) / float(btc['Close'].iloc[-2]) * 100

        mstr = yf.Ticker("MSTR").history(period="5d")
        mstr_price = float(mstr['Close'].iloc[-1])
        mstr_change = (mstr_price - float(mstr['Close'].iloc[-2])) / float(mstr['Close'].iloc[-2]) * 100

        return btc_price, btc_change, mstr_price, mstr_change
    except:
        return None, None, None, None


# --- Dashboard ---
placeholder = st.empty()

while True:
    btc_price, btc_change, mstr_price, mstr_change = get_current_data()
    btc_series, mstr_series = get_historical_data()
    
    with placeholder.container():
        if btc_price is None:
            st.warning("🔄 Lade Daten...")
        else:
            raw_btc = list(btc_series)
            raw_mstr = list(mstr_series)

            ema50_btc = calculate_ema(raw_btc, 50)
            ema200_btc = calculate_ema(raw_btc, 200)
            ema50_mstr = calculate_ema(raw_mstr, 50)
            ema200_mstr = calculate_ema(raw_mstr, 200)

            # Metriken
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("**Bitcoin**", f"${btc_price:,.2f}", f"{btc_change:+.2f}%")
            with col2:
                st.metric("**BTC EMA 50**", f"${ema50_btc:,.2f}" if ema50_btc else "—")
            with col3:
                st.metric("**BTC EMA 200**", f"${ema200_btc:,.2f}" if ema200_btc else "—")

            with col4:
                st.metric("**MSTR**", f"${mstr_price:,.2f}", f"{mstr_change:+.2f}%")
            with col5:
                st.metric("**MSTR EMA 50**", f"${ema50_mstr:,.2f}" if ema50_mstr else "—")
            with col6:
                st.metric("**MSTR EMA 200**", f"${ema200_mstr:,.2f}" if ema200_mstr else "—")

            # Charts
            st.subheader("Bitcoin Kurs + EMAs")
            df_btc = pd.DataFrame({"BTC": raw_btc})
            df_btc["EMA 50"] = [calculate_ema(raw_btc[:i+1], 50) if i >= 49 else None for i in range(len(raw_btc))]
            df_btc["EMA 200"] = [calculate_ema(raw_btc[:i+1], 200) if i >= 199 else None for i in range(len(raw_btc))]
            st.line_chart(df_btc, width='stretch', height=400)

            st.subheader("MSTR Kurs + EMAs")
            df_mstr = pd.DataFrame({"MSTR": raw_mstr})
            df_mstr["EMA 50"] = [calculate_ema(raw_mstr[:i+1], 50) if i >= 49 else None for i in range(len(raw_mstr))]
            df_mstr["EMA 200"] = [calculate_ema(raw_mstr[:i+1], 200) if i >= 199 else None for i in range(len(raw_mstr))]
            st.line_chart(df_mstr, width='stretch', height=400)

            st.subheader("My daily AI Analysis")
            st.markdown(grok_analysis)

            st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')} • konrads.ai")

    time.sleep(90)
