import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from utils.data_loader import load_excel

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Vessel Performance",
    layout="wide"
)

st.markdown("<h2>🚢 Vessel Performance Dashboard</h2>", unsafe_allow_html=True)

# ==================================================
# FILE UPLOAD
# ==================================================
uploaded = st.file_uploader(
    "Upload Noon Report Excel (LogAbstract Sheet)",
    type=["xlsx"]
)

# ==================================================
# HELPERS
# ==================================================
def safe(v):
    return 0.0 if v is None or pd.isna(v) else float(v)


def col_exists(df, col):
    return col in df.columns


# ==================================================
# MAIN APP
# ==================================================
if uploaded:

    df = load_excel(uploaded, "LogAbstract")

    if df.empty:
        st.error("❌ LogAbstract sheet is empty.")
        st.stop()

    st.subheader("📄 Raw Data Preview")
    st.dataframe(df.head(), use_container_width=True)

    # ==================================================
    # DATE RANGE (NO ASSUMPTION ON DATE COLUMN)
    # ==================================================
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("From Date", key="vp_from")
    with col2:
        date_to = st.date_input("To Date", key="vp_to")

    # ==================================================
    # FILTER DATA (SAFE)
    # ==================================================
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[
            (df["Date"].dt.date >= date_from) &
            (df["Date"].dt.date <= date_to)
        ]
    else:
        st.info("ℹ️ No Date column found. Using full dataset.")

    if df.empty:
        st.warning("No records found for selected period.")
        st.stop()

    # ==================================================
    # REQUIRED COLUMNS CHECK
    # ==================================================
    required_cols = [
        "Distance",
        "TimeSincePreviousReport",
        "Sea HFO",
        "Sea MGO",
        "Port HFO",
        "Port MGO",
        "Drifting HFO",
        "Drifting MGO"
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # ==================================================
    # KPI CALCULATIONS
    # ==================================================
    total_distance = df["Distance"].fillna(0).sum()
    total_time = df["TimeSincePreviousReport"].fillna(0).sum()

    avg_speed = (
        total_distance / total_time
        if total_time > 0 else 0
    )

    # Fuel
    total_hfo = (
        df["Sea HFO"].fillna(0).sum() +
        df["Port HFO"].fillna(0).sum() +
        df["Drifting HFO"].fillna(0).sum()
    )

    total_mgo = (
        df["Sea MGO"].fillna(0).sum() +
        df["Port MGO"].fillna(0).sum() +
        df["Drifting MGO"].fillna(0).sum()
    )

    total_fuel = total_hfo + total_mgo

    # SFOC (Fuel per distance)
    sfoc = (
        total_fuel / total_distance
        if total_distance > 0 else 0
    )

    # ==================================================
    # KPI DISPLAY
    # ==================================================
    st.subheader("📊 Key Performance Indicators")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Total Distance", f"{total_distance:.2f} NM")
    k2.metric("Total Time", f"{total_time:.2f} hrs")
    k3.metric("Average Speed", f"{avg_speed:.2f} kn")
    k4.metric("SFOC", f"{sfoc:.3f} MT/NM")

    # ==================================================
    # FUEL SPLIT CHART
    # ==================================================
    st.subheader("⛽ Fuel Consumption Breakdown")

    if total_fuel == 0:
        st.warning("No fuel consumption data.")
    else:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            [total_hfo, total_mgo],
            labels=["HFO", "MGO"],
            autopct=lambda p: f"{p:.1f}%\n({p*total_fuel/100:.1f} MT)",
            startangle=90
        )
        ax.set_title("HFO vs MGO")
        st.pyplot(fig, use_container_width=True)

    # ==================================================
    # TREND CHARTS
    # ==================================================
    st.subheader("📈 Performance Trends")

    if "Date" in df.columns:
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        speed_series = (
            df["Distance"] / df["TimeSincePreviousReport"]
        ).replace([float("inf")], 0)

        ax2.plot(df["Date"], speed_series, marker="o")
        ax2.set_title("Speed Trend")
        ax2.set_ylabel("Knots")
        ax2.set_xlabel("Date")
        st.pyplot(fig2, use_container_width=True)
    else:
        st.info("Date-based trend not available (no Date column).")

else:
    st.info("⬆️ Upload an Excel file to view vessel performance.")
