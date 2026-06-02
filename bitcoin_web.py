import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Bitcoin Monitor", page_icon="₿", layout="wide")

st.title("Konrad's ₿ Live Monitor")
st.markdown("**EMA 50 • EMA 200 • RSI 14 • E-Mail Alert**")

# ==================== DEINE EINSTELLUNGEN ====================
YOUR_EMAIL = "konrad@officeoneuae.com"           
APP_PASSWORD = "hpuj zdbh mdhg dqte"   

# --- Grok AI Analysis ---
grok_analysis = """
**🧠 Grok AI Analysis – 27. Mai 2026**

- Bitcoin hat weiter nachgegeben und notiert aktuell bei ca. 73.400 USD. Der Preis hat in den letzten Tagen die 74k–76k Zone klar unterschritten.
- Death Cross (EMA 50 unter EMA 200) bleibt aktiv.
- Die wichtige Unterstützungszone 68.000 – 70.000 USD rückt immer näher. Diese Marke wird in den nächsten Tagen entscheidend sein.
- Für Langfrist-Investoren: Geduld ist aktuell gefragt.



**Fazit für die nächsten 4–8 Wochen:** Kurzfristig negativ. Die 70k-Marke ist jetzt die wichtigste psychologische und technische Unterstützung. Hält sie, können wir mit einer Stabilisierung rechnen. Bricht sie, muss mit weiteren Rückgängen gerechnet werden. Für dich als Langfrist-Investor bleibt weiterhin Geduld die wichtigste Tugend.








"""

price_history = []

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
    return round(rsi.iloc[-1], 2)

def send_email_alert(subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = YOUR_EMAIL
        msg['To'] = YOUR_EMAIL

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(YOUR_EMAIL, APP_PASSWORD)
        server.sendmail(YOUR_EMAIL, YOUR_EMAIL, msg.as_string())
        server.quit()
        st.success("✅ E-Mail gesendet!")
    except Exception as e:
        st.error(f"E-Mail Fehler: {e}")

def get_data():
    try:
        # Aktueller Preis
        ticker = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=15).json()
        current_price = float(ticker["lastPrice"])
        change24 = float(ticker["priceChangePercent"])

        # Volatility Alert
        global price_history
        now = time.time()
        price_history.append((now, current_price))
        price_history = [x for x in price_history if now - x[0] <= 1800]

        if len(price_history) >= 2:
            oldest_price = price_history[0][1]
            change = ((current_price - oldest_price) / oldest_price) * 100
            if abs(change) >= 0.5:
                direction = "🚀 STARKER ANSTIEG" if change > 0 else "🔻 STARKER RÜCKGANG"
                subject = f"Bitcoin Alert: {direction}"
                body = f"{direction}\n\nVeränderung: {change:+.2f}% in ca. {(now - price_history[0][0])/60:.1f} Minuten\nAktueller Preis: ${current_price:,.2f}"
                send_email_alert(subject, body)

        # Historische Daten (älteste zuerst)
        klines = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": "BTCUSDT", "interval": "1d", "limit": 400},
            timeout=20
        ).json()

        # Close Preise - Binance liefert älteste zuerst
        raw_prices = [float(k[4]) for k in klines]   # älteste zuerst

        def calculate_ema(prices_list, period):
            if len(prices_list) < period:
                return None
            multiplier = 2 / (period + 1)
            ema = sum(prices_list[:period]) / period
            for p in prices_list[period:]:
                ema = (p * multiplier) + (ema * (1 - multiplier))
            return round(ema, 2)

        ema50 = calculate_ema(raw_prices, 50)
        ema200 = calculate_ema(raw_prices, 200)
        rsi14 = calculate_rsi(raw_prices, 14)

        rsi_delta = None
        if rsi14 is not None and len(raw_prices) > 14:
            rsi_yest = calculate_rsi(raw_prices[:-1], 14)
            if rsi_yest is not None:
                rsi_delta = f"{rsi14 - rsi_yest:+.1f}"

        # DataFrame für Chart
        df = pd.DataFrame(klines, columns=["open_time","open","high","low","close","volume","close_time","...","...","...","...","..."])
        df["date"] = pd.to_datetime(df["close_time"], unit="ms")
        df = df.set_index("date")
        df["price"] = df["close"].astype(float)

        df["EMA_50"] = [calculate_ema(raw_prices[:i+1], 50) if i >= 49 else None for i in range(len(raw_prices))]
        df["EMA_200"] = [calculate_ema(raw_prices[:i+1], 200) if i >= 199 else None for i in range(len(raw_prices))]

        return current_price, change24, ema50, ema200, rsi14, rsi_delta, df

    except Exception as e:
        print(f"Fehler: {e}")
        return None, None, None, None, None, None, None


# --- Dashboard ---
placeholder = st.empty()

while True:
    price, change24, ema50, ema200, rsi14, rsi_delta, df = get_data()
    
    with placeholder.container():
        if price is not None and df is not None:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
            
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
                    if rsi14 > 70:
                        st.metric("**RSI 14**", f"{rsi14}", rsi_delta, delta_color="inverse")
                    elif rsi14 < 30:
                        st.metric("**RSI 14**", f"{rsi14}", rsi_delta, delta_color="normal")
                    else:
                        st.metric("**RSI 14**", f"{rsi14}", rsi_delta)
            
            with col5:
                status = "🟢 Bullish" if price > ema200 else "🔴 Bearish"
                st.markdown(f"**Status:** {status}")

            st.subheader("Bitcoin Kurs + EMAs - Letzte 12 Monate")
            chart_data = df[["price", "EMA_50", "EMA_200"]]
            st.line_chart(chart_data, width='stretch', height=520)

            st.subheader("My daily AI Analysis")
            st.markdown(grok_analysis)

            st.caption(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')} • Test-Modus")
        else:
            st.warning("🔄 Lade Daten...")
    
    time.sleep(120)