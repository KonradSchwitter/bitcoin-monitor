import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Konrad's Monitor", page_icon="₿", layout="wide")

st.title("₿ konrads.ai — Live Monitor")
st.markdown("**Bitcoin • MicroStrategy (MSTR) • Vergleich**")

# --- Grok AI Analysis ---
grok_analysis = """
**🧠 Grok AI Analysis – 03. Juni 2026**

- Bitcoin bewegt sich weiter in der Korrekturzone unter 70k.
- MSTR als leveraged BTC-Play zeigt stärkere Schwankungen.
- Langfristig bleibt die Strategie: Geduld und schrittweises Nachkaufen.
"""

def get_data():
    try:
        # BTC Daten
        btc = yf.Ticker("BTC-USD")
        btc_info = btc.history(period="5d")
        btc_price = float(btc_info['Close'].iloc[-1])
        btc_change = (btc_price - float(btc_info['Close'].iloc[-2])) / float(btc_info['Close'].iloc[-2]) * 100

        # MSTR Daten
        mstr = yf.Ticker("MSTR")
        mstr_info = mstr.history(period="5d")
        mstr_price = float(mstr_info['Close'].iloc[-1])
        mstr_change = (mstr_price - float(mstr_info['Close'].iloc[-2])) / float(mstr_info['Close'].iloc[-2]) * 100

        # Historische Daten für Chart (letzte 12 Monate)
        hist = yf.download(["BTC-USD", "MSTR"], period="1y", interval="1d")
        df = hist['Close'].copy()
        df.columns = ['BTC', 'MSTR']

        # Normierung auf 100 für besseren Vergleich
        df_norm = df / df.iloc[0] * 100

        return btc_price, btc_change, mstr_price, mstr_change, df_norm

    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        return None, None, None, None, None


# --- Dashboard ---
placeholder = st.empty()

while True:
    btc_price, btc_change, mstr_price, mstr_change, df_norm = get_data()
    
    with placeholder.container():
        if btc_price is not None:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("**Bitcoin (BTC)**", f"${btc_price:,.2f}", f"{btc_change:+.2f}%")
            
            with col2:
                st.metric("**MicroStrategy (MSTR)**", f"${mstr_price:,.2f}", f"{mstr_change:+.2f}%")
            
            with col3:
                mstr_premium = ((mstr_price / btc_price) * 100) if btc_price > 0 else 0
                st.metric("**MSTR Premium**", f"{mstr_premium:.1f}x", "")
            
            with col4:
                status = "🟢 Bullish" if btc_change > 0 else "🔴 Bearish"
                st.markdown(f"**Status:** {status}")

            st.subheader("Vergleich BTC vs MSTR (normiert auf 100)")
            st.line_chart(df_norm, width='stretch', height=520)

            st.subheader("My daily AI Analysis")
            st.markdown(grok_analysis)

            st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')} • konrads.ai")
        else:
            st.warning("🔄 Lade Daten...")

    time.sleep(60)
