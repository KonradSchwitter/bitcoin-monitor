import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="konrads.ai", page_icon="₿", layout="wide")

st.title("konrads.ai — Live Monitor")

tab1, tab2 = st.tabs(["Bitcoin Monitor", "MSTR Monitor"])


@st.cache_data(ttl=300)
def load_data(symbol):
    df = yf.download(
        symbol,
        period="3y",          # 3 Jahre für stabile EMA200
        interval="1d",
        auto_adjust=True,
        progress=False
    )
    if df.empty:
        raise ValueError(f"Keine Daten für {symbol}")
    
    # MultiIndex entfernen falls vorhanden
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

        # EMA Berechnung (sehr sauber)
        df["EMA_50"] = close.ewm(span=50, adjust=False).mean()
        df["EMA_200"] = close.ewm(span=200, adjust=False).mean()

        ema50 = float(df["EMA_50"].iloc[-1])
        ema200 = float(df["EMA_200"].iloc[-1])

        # Status
        status = "🟢 Bullish" if current_price > ema200 else "🔴 Bearish"

        # Metriken
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        with col1:
            st.metric(f"{title} Preis", f"${current_price:,.2f}", f"{daily_change:+.2f}%")
        with col2:
            st.metric("EMA 50", f"${ema50:,.2f}")
        with col3:
            st.metric("EMA 200", f"${ema200:,.2f}")
        with col4:
            if status == "🟢 Bullish":
                st.success(status)
            else:
                st.error(status)

        # Chart
        chart_df = df.tail(365).reset_index()
        chart_df = chart_df.rename(columns={"index": "Date"} if "index" in chart_df.columns else {"Date": "Date"})

        chart_data = chart_df.melt(
            id_vars=["Date"],
            value_vars=["Close", "EMA_50", "EMA_200"],
            var_name="Linie",
            value_name="Wert"
        )

        chart = (
            alt.Chart(chart_data)
            .mark_line(strokeWidth=2.5)
            .encode(
                x=alt.X("Date:T", title="Datum"),
                y=alt.Y("Wert:Q", title="Preis (USD)"),
                color=alt.Color(
                    "Linie:N",
                    scale=alt.Scale(
                        domain=["Close", "EMA_50", "EMA_200"],
                        range=["#4FC3F7", "#FFA726", "#EF5350"]
                    ),
                    legend=alt.Legend(title="Linie")
                ),
                tooltip=[
                    alt.Tooltip("Date:T", title="Datum"),
                    alt.Tooltip("Linie:N", title="Linie"),
                    alt.Tooltip("Wert:Q", title="Wert", format=",.2f")
                ]
            )
            .interactive()
        )

        st.subheader(f"{title} Kurs + EMAs - Letzte 12 Monate")
        st.altair_chart(chart, use_container_width=True)

        st.caption(f"Datenpunkte: {len(df)} | Aktualisiert: {datetime.now().strftime('%H:%M:%S')}")

    except Exception as e:
        st.error(f"Fehler bei {title}: {str(e)}")


# Tabs aufrufen
with tab1:
    show_monitor("BTC-USD", "Bitcoin")

with tab2:
    show_monitor("MSTR", "MicroStrategy")

st.caption("konrads.ai • Powered by yfinance + Altair")
