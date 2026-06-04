import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# --------------------------------------------------
# Streamlit Setup
# --------------------------------------------------
st.set_page_config(
    page_title="konrads.ai",
    page_icon="₿",
    layout="wide"
)

st.title("konrads.ai — Live Monitor")

tab1, tab2 = st.tabs([
    "Bitcoin Monitor",
    "MSTR Monitor"
])

# --------------------------------------------------
# Daten laden (Cache 5 Minuten)
# --------------------------------------------------
@st.cache_data(ttl=300)
def load_data(symbol):
    df = yf.download(
        symbol,
        period="3y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        raise ValueError(f"Keine Daten für {symbol} gefunden.")

    return df


# --------------------------------------------------
# Monitor-Funktion
# --------------------------------------------------
def show_monitor(symbol, title):

    try:
        df = load_data(symbol)

        # --------------------------------------------------
        # Preise
        # --------------------------------------------------
        current_price = float(df["Close"].iloc[-1])
        previous_price = float(df["Close"].iloc[-2])

        daily_change = (
            (current_price - previous_price)
            / previous_price
        ) * 100

        # --------------------------------------------------
        # EMA Berechnung
        # --------------------------------------------------
        df["EMA_50"] = (
            df["Close"]
            .ewm(span=50, adjust=False)
            .mean()
        )

        df["EMA_200"] = (
            df["Close"]
            .ewm(span=200, adjust=False)
            .mean()
        )

        ema50 = float(df["EMA_50"].iloc[-1])
        ema200 = float(df["EMA_200"].iloc[-1])

        # --------------------------------------------------
        # Trendstatus
        # --------------------------------------------------
        golden_cross = ema50 > ema200

        # --------------------------------------------------
        # Kennzahlen
        # --------------------------------------------------
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

        with col1:
            st.metric(
                f"{title} Preis",
                f"${current_price:,.2f}",
                f"{daily_change:+.2f}%"
            )

        with col2:
            st.metric(
                "EMA 50",
                f"${ema50:,.2f}"
            )

        with col3:
            st.metric(
                "EMA 200",
                f"${ema200:,.2f}"
            )

        with col4:
            if golden_cross:
                st.success("🟢 Golden Cross")
            else:
                st.error("🔴 Death Cross")

        st.divider()

        # --------------------------------------------------
        # Chart Daten (letzte 12 Monate)
        # --------------------------------------------------
        chart_df = df.tail(365).copy()

        chart_df = (
            chart_df[["Close", "EMA_50", "EMA_200"]]
            .reset_index()
            .rename(columns={"Close": "Price"})
        )

        chart_data = chart_df.melt(
            id_vars=["Date"],
            value_vars=["Price", "EMA_50", "EMA_200"],
            var_name="Linie",
            value_name="Wert"
        )

        chart = (
            alt.Chart(chart_data)
            .mark_line(strokeWidth=2)
            .encode(
                x=alt.X(
                    "Date:T",
                    title="Datum"
                ),
                y=alt.Y(
                    "Wert:Q",
                    title="Preis"
                ),
                color=alt.Color(
                    "Linie:N",
                    scale=alt.Scale(
                        domain=[
                            "Price",
                            "EMA_50",
                            "EMA_200"
                        ],
                        range=[
                            "#FFFFFF",  # Preis
                            "#FFA500",  # EMA50
                            "#FF4040"   # EMA200
                        ]
                    )
                ),
                tooltip=[
                    alt.Tooltip(
                        "Date:T",
                        title="Datum"
                    ),
                    alt.Tooltip(
                        "Linie:N",
                        title="Linie"
                    ),
                    alt.Tooltip(
                        "Wert:Q",
                        title="Wert",
                        format=",.2f"
                    )
                ]
            )
            .interactive()
        )

        st.subheader(
            f"{title} Kurs + EMA50 + EMA200 (letzte 12 Monate)"
        )

        st.altair_chart(
            chart,
            use_container_width=True
        )

        st.caption(
            f"Historische Datenpunkte: {len(df):,}"
        )

    except Exception as e:
        st.error(
            f"Fehler bei {title}: {str(e)}"
        )


# --------------------------------------------------
# TAB 1 - BITCOIN
# --------------------------------------------------
with tab1:
    st.subheader("Bitcoin Monitor")
    show_monitor(
        "BTC-USD",
        "Bitcoin"
    )

# --------------------------------------------------
# TAB 2 - MSTR
# --------------------------------------------------
with tab2:
    st.subheader("MSTR Monitor")
    show_monitor(
        "MSTR",
        "MSTR"
    )

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.caption(
    f"Aktualisiert um "
    f"{datetime.now().strftime('%H:%M:%S')} "
    f"• konrads.ai"
)
