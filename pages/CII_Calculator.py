import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from utils.cii_utils import calculate_cii, classify_operation_by_events_in_range
from utils.data_loader import load_excel

st.set_page_config(page_title="CII Calculator", layout="wide")

st.markdown("<h2 class='mt-4'>📘 CII CALCULATOR</h2>", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload Noon Report Excel (LogAbstract Sheet)", type=["xlsx"])

ship_type = st.selectbox(
    "Select Ship Type",
    ["Bulk Carrier", "Tanker", "Container", "RoRo", "General Cargo", "Cable Layer"],
    key="ship_type_selectbox"
)

if uploaded:

    df = load_excel(uploaded, "LogAbstract")

    if df.empty:
        st.error("No data found in the LogAbstract sheet.")
        st.stop()

    # -----------------------
    # DEADWEIGHT INPUT
    # -----------------------
    dwt = st.number_input(
        "Enter Deadweight (DWT in tonnes)",
        min_value=1000.0,
        value=50000.0,
        step=100.0,
        key="dwt_input"
    )

    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("From Date", key="date_from_input")
    with col2:
        date_to = st.date_input("To Date", key="date_to_input")

    if st.button("Calculate CII"):
        # ------------------------
        # CII CALCULATION
        # ------------------------
        filtered, result = calculate_cii(df, ship_type, date_from, date_to, dwt=dwt)
        st.success("Calculation Complete!")

        st.write("### Filtered Operational Data")
        st.dataframe(filtered, use_container_width=True)

        st.write("### Final CII Results")
        st.json(result)

        # ------------------------
        # OPERATIONAL BREAKDOWN
        # ------------------------
        st.write("## ⚓ Operational Breakdown Based on Events (Sea / Port / Drifting)")

        ops = classify_operation_by_events_in_range(df, date_from, date_to)
        st.json(ops)

        # ------------------------
        # PIE CHARTS
        # ------------------------
        # Hours distribution
        labels_hours = ["Sea", "Port", "Drifting"]
        values_hours = [ops["Sea Hours"], ops["Port Hours"], ops["Drifting Hours"]]

        fig1, ax1 = plt.subplots()
        ax1.pie(values_hours, labels=labels_hours, autopct="%1.1f%%", startangle=90)
        ax1.set_title("Hours Distribution")
        st.pyplot(fig1)

        # Fuel distribution
        values_fuel = [
            ops.get("Sea Fuel HFO", 0) + ops.get("Sea Fuel MGO", 0),
            ops.get("Port Fuel HFO", 0) + ops.get("Port Fuel MGO", 0),
            ops.get("Drifting Fuel HFO", 0) + ops.get("Drifting Fuel MGO", 0)
        ]

        labels_fuel = ["Sea", "Port", "Drifting"]

        fig2, ax2 = plt.subplots()
        ax2.pie(values_fuel, labels=labels_fuel, autopct="%1.1f%%", startangle=90)
        ax2.set_title("Fuel Consumption Distribution")
        st.pyplot(fig2)

else:
    st.info("Please upload an Excel file to begin.")
