import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, time as dtime

# ---------------------------------------------------------
# CII Utils
# ---------------------------------------------------------
CII_FACTORS = {
    "HFO": 3.114,
    "MGO": 3.206,
    "LFO": 3.151,
    "LNG": 2.75,
}

REFERENCE_PARAMS = {
    "Bulk Carrier": (4745, 0.622),
    "Tanker": (5247, 0.610),
    "Container": (1984, 0.489),
    "General Cargo <20k": (588, 0.3885),
    "General Cargo ≥20k": (31948, 0.792),
}

REDUCTION_FACTORS = {
    2023: 0.05,
    2024: 0.07,
    2025: 0.09,
    2026: 0.11,
    2027: 0.13,
    2028: 0.15,
}

# -----------------------------
# CII Calculation
# -----------------------------
def calculate_cii(df, ship_type, date_from, date_to, dwt=0):
    df["DateUTC"] = pd.to_datetime(df["DateUTC"], errors="coerce").dt.date
    filtered = df[(df["DateUTC"] >= date_from) & (df["DateUTC"] <= date_to)]

    distance = filtered.get("Distance", pd.Series([0])).sum()

    fuel_cols = [
        "MEConsumptionHFO", "MEConsumptionMGO",
        "AEConsumptionHFO", "AEConsumptionMGO",
        "BoilerConsumptionHFO", "BoilerConsumptionMGO",
        "IGSConsumptionHFO", "IGSConsumptionMGO"
    ]
    for col in fuel_cols:
        filtered[col] = pd.to_numeric(filtered.get(col, 0), errors='coerce').fillna(0)

    total_fuel = round(filtered[fuel_cols].sum().sum(), 3)

    co2 = (
        filtered["MEConsumptionHFO"].sum() * CII_FACTORS["HFO"] +
        filtered["MEConsumptionMGO"].sum() * CII_FACTORS["MGO"] +
        filtered["AEConsumptionHFO"].sum() * CII_FACTORS["HFO"] +
        filtered["AEConsumptionMGO"].sum() * CII_FACTORS["MGO"] +
        filtered["BoilerConsumptionHFO"].sum() * CII_FACTORS["HFO"] +
        filtered["BoilerConsumptionMGO"].sum() * CII_FACTORS["MGO"] +
        filtered["IGSConsumptionHFO"].sum() * CII_FACTORS["HFO"] +
        filtered["IGSConsumptionMGO"].sum() * CII_FACTORS["MGO"]
    )

    if dwt == 0:
        dwt = filtered["DraftDisplacementActual"].iloc[0] if "DraftDisplacementActual" in filtered.columns else 50000

    attained_aer = (co2 / (dwt * distance)) * 1_000_000 if distance > 0 else 0

    year = date_to.year
    reduction_factor = REDUCTION_FACTORS.get(year, 0.09)

    if ship_type == "Cable Layer":
        a, c = REFERENCE_PARAMS["General Cargo <20k"]
    else:
        a, c = REFERENCE_PARAMS[ship_type]

    cii_ref = a * (dwt ** (-c))
    required_aer_value = (1 - reduction_factor) * cii_ref

    if attained_aer <= 0.75 * required_aer_value:
        rating = "A"
    elif attained_aer <= 0.90 * required_aer_value:
        rating = "B"
    elif attained_aer <= required_aer_value:
        rating = "C"
    elif attained_aer <= 1.10 * required_aer_value:
        rating = "D"
    else:
        rating = "E"

    return filtered, {
        "calculation_period": f"{date_from} to {date_to}",
        "Distance (NM)": distance,
        "Total Fuel (MT)": total_fuel,
        "Total CO2 (MT)": round(co2, 3),
        "DWT Used": dwt,
        "Attained AER": round(attained_aer, 3),
        "Required AER": round(required_aer_value, 3),
        "CII Rating": rating
    }

# -----------------------------
# Operational Classification
# -----------------------------
def classify_operation_by_events_in_range(df, date_from, date_to):
    df = df.copy()

    # Required columns
    fuel_cols = [
        "MEConsumptionHFO","AEConsumptionHFO","BoilerConsumptionHFO",
        "MEConsumptionMGO","AEConsumptionMGO","BoilerConsumptionMGO"
    ]
    for c in fuel_cols:
        df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0)

    df["DateTimeInUTC"] = pd.to_datetime(df["DateTimeInUTC"], errors="coerce")
    df = df.sort_values("DateTimeInUTC").reset_index(drop=True)

    start_dt = datetime.combine(pd.to_datetime(date_from).date(), dtime.min)
    end_dt = datetime.combine(pd.to_datetime(date_to).date(), dtime.max)
    mask = (df["DateTimeInUTC"] >= start_dt) & (df["DateTimeInUTC"] <= end_dt)
    filtered = df.loc[mask].reset_index(drop=True)

    if filtered.empty:
        return {k:0 for k in ["Sea Hours","Port Hours","Drifting Hours","Sea HFO","Port HFO","Drifting HFO","Sea MGO","Port MGO","Drifting MGO"]}

    SEA = {"Arrival", "Departure", "Noon (Sea)"}
    PORT = {"Shifting to Berth", "Idle In Port", "IDLE IN PORT", "Discharging", "Loading", "LOADING"}
    DRIFT = {"Drifting", "Awaiting Orders", "Stopping Engine"}

    sea_h = port_h = drift_h = 0
    sea_hfo = port_hfo = drift_hfo = 0
    sea_mgo = port_mgo = drift_mgo = 0

    for i, row in filtered.iterrows():
        if i == 0:
            interval = 0
        else:
            prev_time = filtered.loc[i-1, "DateTimeInUTC"]
            interval = row["TimeSincePreviousReport"]

        row_hfo = row["MEConsumptionHFO"] + row["AEConsumptionHFO"] + row["BoilerConsumptionHFO"]
        row_mgo = row["MEConsumptionMGO"] + row["AEConsumptionMGO"] + row["BoilerConsumptionMGO"]

        event = str(row["EventType"]).strip()
        if event in SEA:
            sea_h += interval
            sea_hfo += row_hfo
            sea_mgo += row_mgo
        elif event in PORT:
            port_h += interval
            port_hfo += row_hfo
            port_mgo += row_mgo
        elif event in DRIFT:
            drift_h += interval
            drift_hfo += row_hfo
            drift_mgo += row_mgo

    return {
        "Sea Hours": round(sea_h,2),
        "Port Hours": round(port_h,2),
        "Drifting Hours": round(drift_h,2),
        "Sea HFO": round(sea_hfo,3),
        "Port HFO": round(port_hfo,3),
        "Drifting HFO": round(drift_hfo,3),
        "Sea MGO": round(sea_mgo,3),
        "Port MGO": round(port_mgo,3),
        "Drifting MGO": round(drift_mgo,3)
    }

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="CII & Operations Dashboard", layout="wide")
st.title("📘 CII Calculator & Operational Analysis")

uploaded = st.file_uploader("Upload Noon Report Excel", type=["xlsx"])
ship_type = st.selectbox(
    "Select Ship Type",
    ["Bulk Carrier", "Tanker", "Container", "RoRo", "General Cargo", "Cable Layer"]
)
dwt = st.number_input("Deadweight (DWT in tonnes)", min_value=1000.0, value=50000.0, step=100.0)

col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input("From Date")
with col2:
    date_to = st.date_input("To Date")

if uploaded and st.button("Calculate CII & Operations"):
    df = pd.read_excel(uploaded, sheet_name="LogAbstract")
    filtered, cii_result = calculate_cii(df, ship_type, date_from, date_to, dwt=dwt)
    ops_result = classify_operation_by_events_in_range(df, date_from, date_to)

    st.subheader("✅ CII Results")
    st.json(cii_result)

    st.subheader("⚓ Operational Breakdown (Hours & Consumption)")
    st.json(ops_result)

    # -----------------------------
    # Hours Pie Chart
    # -----------------------------
    labels = ["Sea", "Port", "Drifting"]
    sizes = [ops_result["Sea Hours"], ops_result["Port Hours"], ops_result["Drifting Hours"]]

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax1.set_title("Hours Distribution")
    st.pyplot(fig1)

    # -----------------------------
    # Fuel Bar Chart
    # -----------------------------
    fuel_data = pd.DataFrame({
        "HFO": [ops_result["Sea HFO"], ops_result["Port HFO"], ops_result["Drifting HFO"]],
        "MGO": [ops_result["Sea MGO"], ops_result["Port MGO"], ops_result["Drifting MGO"]]
    }, index=["Sea","Port","Drifting"])
    st.subheader("⚡ Fuel Consumption (MT)")
    st.bar_chart(fuel_data)
