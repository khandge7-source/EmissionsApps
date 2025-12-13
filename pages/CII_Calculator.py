import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from utils.cii_utils import calculate_cii, classify_operation_by_events_in_range
from utils.data_loader import load_excel

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="CII Calculator", layout="wide")

st.markdown("<h2>📘 CII CALCULATOR</h2>", unsafe_allow_html=True)

# ==================================================
# FILE UPLOAD
# ==================================================
uploaded = st.file_uploader(
    "Upload Noon Report Excel (LogAbstract Sheet)",
    type=["xlsx"]
)

ship_type = st.selectbox(
    "Select Ship Type",
    [
        "Bulk Carrier",
        "Tanker",
        "Container",
        "RoRo",
        "General Cargo",
        "Cable Layer"
    ],
    key="ship_type"
)

# ==================================================
# HELPERS
# ==================================================
def safe(v):
    """Convert NaN / None to 0"""
    return 0.0 if v is None or pd.isna(v) else float(v)


def autopct_with_values(values, unit=""):
    """Show value + percentage on pie chart"""
    total = sum(values)

    def _autopct(pct):
        val = pct * total / 100.0
        if val <= 0:
            return ""
        return f"{val:.1f}{unit}\n({pct:.1f}%)"

    return _autopct


# ==================================================
# MAIN APP
# ==================================================
if uploaded:

    df = load_excel(uploaded, "LogAbstract")

    if df.empty:
        st.error("❌ No data found in LogAbstract sheet.")
        st.stop()

    # ---------------- DWT ----------------
    dwt = st.number_input(
        "Enter Deadweight (DWT in tonnes)",
        min_value=1000.0,
        value=50000.0,
        step=100.0,
        key="dwt"
    )

    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("From Date", key="date_from")
    with col2:
        date_to = st.date_input("To Date", key="date_to")

    # ==================================================
    # CALCULATE
    # ==================================================
    if st.button("🚀 Calculate CII", key="calc_btn"):

        # ---------------- CII ----------------
        filtered, result = calculate_cii(
            df, ship_type, date_from, date_to, dwt=dwt
        )

        st.success("✅ Calculation Complete")

        st.subheader("📄 Filtered Operational Data")
        st.dataframe(filtered, use_container_width=True)

        st.subheader("📊 Final CII Results")
        st.json(result)

        # ---------------- OPERATIONS ----------------
        st.subheader("⚓ Operational Breakdown")

        ops = classify_operation_by_events_in_range(
            df, date_from, date_to
        )

        st.json(ops)

        # ==================================================
        # HOURS
        # ==================================================
        sea_h = safe(ops.get("Sea Hours"))
        port_h = safe(ops.get("Port Hours"))
        drift_h = safe(ops.get("Drifting Hours"))

        values_hours = [sea_h, port_h, drift_h]
        labels_hours = ["Sea", "Port", "Drifting"]

        # ==================================================
        # FUEL (CORRECT KEYS)
        # ==================================================
        sea_fuel = safe(ops.get("Sea HFO")) + safe(ops.get("Sea MGO"))
        port_fuel = safe(ops.get("Port HFO")) + safe(ops.get("Port MGO"))
        drift_fuel = safe(ops.get("Drifting HFO")) + safe(ops.get("Drifting MGO"))

        # HFO vs MGO
        total_hfo = (
            safe(ops.get("Sea HFO")) +
            safe(ops.get("Port HFO")) +
            safe(ops.get("Drifting HFO"))
        )

        total_mgo = (
            safe(ops.get("Sea MGO")) +
            safe(ops.get("Port MGO")) +
            safe(ops.get("Drifting MGO"))
        )

        # ==================================================
        # CHARTS
        # ==================================================
        st.subheader("📈 Operational Distribution")

        c1, c2 = st.columns(2)

        # ---------- HOURS PIE ----------
        with c1:
            st.markdown("#### ⏱ Hours Distribution")

            if sum(values_hours) == 0:
                st.warning("No hours data available.")
            else:
                fig1, ax1 = plt.subplots(figsize=(3.8, 3.8))
                ax1.pie(
                    values_hours,
                    labels=labels_hours,
                    autopct=autopct_with_values(values_hours, " h"),
                    startangle=90,
                    textprops={"fontsize": 9}
                )
                ax1.set_title("Sea / Port / Drifting", fontsize=11)
                st.pyplot(fig1, use_container_width=True)

        # ---------- FUEL PIE ----------
        with c2:
            st.markdown("#### ⛽ Fuel Consumption (HFO vs MGO)")

            fuel_values = [total_hfo, total_mgo]
            fuel_labels = ["HFO", "MGO"]

            if sum(fuel_values) == 0:
                st.warning("No fuel data available.")
            else:
                fig2, ax2 = plt.subplots(figsize=(3.8, 3.8))
                ax2.pie(
                    fuel_values,
                    labels=fuel_labels,
                    autopct=autopct_with_values(fuel_values, " MT"),
                    startangle=90,
                    textprops={"fontsize": 9}
                )
                ax2.set_title("Fuel Split", fontsize=11)
                st.pyplot(fig2, use_container_width=True)

else:
    st.info("⬆️ Upload an Excel file to begin.")
