import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Bitcoin Monitor", page_icon="₿", layout="wide")

st.title("₿ Konrad's Bitcoin Live Monitor")
st.markdown("**EMA 50 • EMA 200 • RSI 14**")

# --- Grok AI Analysis ---
grok_analysis = """
**🧠 Grok AI Analysis – 02. Juni 2026**

- Bitcoin notiert aktuell unter 70k.
- Death Cross aktiv.
- Nächste wichtige Unterstützung bei 65k–68k.
- Langfristig: Geduld ist gefragt.
"""

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
        # Einfacherer API-Call mit längeren Timeouts
        ticker = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", 
            timeout=20
        ).json()
        
        current_price = float(ticker["lastPrice"])
        change24 = float(ticker["priceChangePercent"])

        # Historische Daten
        klines = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": "BTCUSDT", "interval": "1d", "limit": 300},
            timeout=20
        ).json()

        raw_prices = [float(k[4]) for k in klines]

        def calculate_ema(prices_list, period):
            if len(prices_list) < period:
                return None
            multiplier = 2 / (period + 1)
            ema = sum(prices_list[:period]) / period
            for p in prices_list[period:]:
                ema = (p * multiplier) + (ema * (1 - multiplier))
            return round(ema, 2)

        ema50 = calculate_ema(raw_prices[::-1], 50)
        ema200 = calculate_ema(raw_prices[::-1], 200)
        rsi14 = calculate_rsi(raw_prices, 14)

        df = pd.DataFrame(klines, columns=["open_time","open","high","low","close","volume","close_time","...","...","...","...","..."])
        df["date"] = pd.to_datetime(df["close_time"], unit="ms")
        df = df.set_index("date")
        df["price"] = df["close"].astype(float)

        return current_price, change24, ema50, ema200, rsi14, df

    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None, None, None, None, None, None


placeholder = st.empty()

while True:
    price, change24, ema50, ema200, rsi14, df = get_data()
    
    with placeholder.container():
        if price is not None:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("**Bitcoin Preis**", f"${price:,.2f}", f"{change24:+.2f}%")
            
            with col2:
                if ema50:
                    diff50 = price - ema50
                    pct50 = (diff50 / ema50) * 100 if ema50 else 0
                    st.metric("**EMA 50**", f"${ema50:,.2f}", f"{pct50:+.2f}%")
            
            with col3:
                if ema200:
                    diff200 = price - ema200
                    pct200 = (diff200 / ema200) * 100
                    st.metric("**EMA 200**", f"${ema200:,.2f}", f"{pct200:+.2f}%")
            
            with col4:
                if rsi14 is not None:
                    st.metric("**RSI 14**", f"{rsi14}")
            
            st.subheader("Bitcoin Kurs + EMAs - Letzte 12 Monate")
            chart_data = df[["price", "EMA_50", "EMA_200"]].dropna(how='all')
            st.line_chart(chart_data, width='stretch', height=520)

            st.subheader("My daily AI Analysis")
            st.markdown(grok_analysis)

            st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning("🔄 Versuche Daten zu laden... (API manchmal langsam)")
    
    time.sleep(60)
