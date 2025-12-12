import streamlit as st
import pandas as pd
from utils.cii_utils import calculate_cii
from utils.data_loader import load_excel

st.set_page_config(page_title="CII Calculator", layout="wide")

st.markdown("<h2 class='mt-4'>📘 CII CALCULATOR</h2>", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload Noon Report Excel (LogAbstract Sheet)", type=["xlsx"])

ship_type = st.selectbox(
    "Select Ship Type",
    ["Bulk Carrier", "Tanker", "Container", "RoRo", "General Cargo", "Cable Layer"]
)

if uploaded:
    df = load_excel(uploaded, "LogAbstract")

    if df.empty:
        st.error("No data found in the LogAbstract sheet.")
        st.stop()

    # Add Deadweight input field
    dwt = st.number_input(
        "Enter Deadweight (DWT in tonnes)",
        min_value=1000.0,
        value=50000.0,
        step=100.0
    )

    col1, col2 = st.columns(2)

    with col1:
        date_from = st.date_input("From Date")
    with col2:
        date_to = st.date_input("To Date")

    if st.button("Calculate CII"):
        # Pass DWT to the calculation
        filtered, result = calculate_cii(df, ship_type, date_from, date_to, dwt=dwt)

        st.success("Calculation Complete!")

        st.write("### Filtered Operational Data")
        st.dataframe(filtered, use_container_width=True)

        st.write("### Final CII Results")
        st.json(result)
