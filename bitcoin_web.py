import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="konrads.ai", page_icon="₿", layout="wide")

st.title("konrads.ai — Live Monitor")

tab1, tab2 = st.tabs(["Bitcoin Monitor", "MSTR Monitor"])

# ==================== EINSTELLUNGEN ====================
YOUR_EMAIL = "konrad@officeoneuae.com"
APP_PASSWORD = "hpuj zdbh mdhg dqte"
ALERT_PERCENT = 0.8          # E-Mail bei ±0.8% Veränderung in kurzer Zeit
price_history = {"BTC-USD": [], "MSTR": []}

def send_email_alert(title, price, change):
    try:
        msg = MIMEText(f"{title} hat sich um {change:+.2f}% bewegt.\nAktueller Preis: ${price:,.2f}")
        msg['Subject'] = f"ALARM: {title} {change:+.2f}%"
        msg['From'] = YOUR_EMAIL
        msg['To'] = YOUR_EMAIL

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(YOUR_EMAIL, APP_PASSWORD)
        server.sendmail(YOUR_EMAIL, YOUR_EMAIL, msg.as_string())
        server.quit()
        st.success(f"✅ E-Mail-Alarm gesendet ({title})")
    except:
        pass  # leise fehlschlagen im Live-Betrieb

@st.cache_data(ttl=300)
def load_data(symbol):
    df = yf.download(symbol, period="3y", interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def show_monitor(symbol, title):
    try:
        df = load_data(symbol)
        close = df["Close"].copy()

        current_price = float(close.iloc[-1])
        previous_price = float(close.iloc[-2])
        daily_change = (current_price - previous_price) / previous_price * 100

        # EMA
        df["EMA_50"] = close.ewm(span=50, adjust=False).mean()
        df["EMA_200"] = close.ewm(span=200, adjust=False).mean()

        ema50 = float(df["EMA_50"].iloc[-1])
        ema200 = float(df["EMA_200"].iloc[-1])

        # Alert prüfen
        price_history[symbol].append(current_price)
        if len(price_history[symbol]) > 5:  # kurze Historie
            old_price = price_history[symbol][-5]
            short_change = (current_price - old_price) / old_price * 100
            if abs(short_change) >= ALERT_PERCENT:
                send_email_alert(title, current_price, short_change)

        # Layout
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        with col1:
            st.metric(f"{title} Preis", f"${current_price:,.2f}", f"{daily_change:+.2f}%")
        with col2:
            st.metric("EMA 50", f"${ema50:,.2f}")
        with col3:
            st.metric("EMA 200", f"${ema200:,.2f}")
        with col4:
            status = "🟢 Bullish" if current_price > ema200 else "🔴 Bearish"
            if status == "🟢 Bullish":
                st.success(status)
            else:
                st.error(status)

        # Altair Chart
        chart_df = df.tail(365).reset_index()
        chart_data = chart_df.melt(
            id_vars=["Date"],
            value_vars=["Close", "EMA_50", "EMA_200"],
            var_name="Linie",
            value_name="Wert"
        )

        chart = alt.Chart(chart_data).mark_line(strokeWidth=2.5).encode(
            x=alt.X("Date:T", title="Datum"),
            y=alt.Y("Wert:Q", title="Preis (USD)"),
            color=alt.Color("Linie:N", scale=alt.Scale(
                domain=["Close", "EMA_50", "EMA_200"],
                range=["#4FC3F7", "#FFA726", "#EF5350"]
            )),
            tooltip=["Date:T", "Linie:N", alt.Tooltip("Wert:Q", format=",.2f")]
        ).interactive()

        st.subheader(f"{title} Kurs + EMA50 + EMA200")
        st.altair_chart(chart, use_container_width=True)

        st.caption(f"Datenpunkte: {len(df)} | Aktualisiert: {datetime.now().strftime('%H:%M:%S')}")

    except Exception as e:
        st.error(f"Fehler bei {title}: {str(e)}")
# Tabs
with tab1:
    show_monitor("BTC-USD", "Bitcoin")

with tab2:
    show_monitor("MSTR", "MicroStrategy")

# Live Refresh
if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0

st.session_state.refresh_counter += 1
time.sleep(60)          # alle 60 Sekunden neu laden
st.rerun()

