import pandas as pd

CII_FACTORS = {
    "HFO": 3.114,
    "MGO": 3.206,
    "LFO": 3.151,
    "LNG": 2.75,
}

REQUIRED_AER_2025 = {
    "Bulk Carrier": 4.23,
    "Tanker": 5.05,
    "Container": 15.55,
    "RoRo": 6.0,
    "General Cargo": 7.0,
    "Cable Layer": 3.88,  # Custom assumption
}

def calculate_cii(df, ship_type, date_from, date_to, dwt=0):
    # Convert date
    df["DateUTC"] = pd.to_datetime(df["DateUTC"]).dt.date

    # Filter by date
    filtered = df[(df["DateUTC"] >= date_from) & (df["DateUTC"] <= date_to)]

    # Total distance
    distance = filtered["Distance"].sum() if "Distance" in filtered.columns else 0

    # Total fuel
    fuel_cols = [
        "MEConsumptionHFO",
        "MEConsumptionMGO",
        "AEConsumptionHFO",
        "AEConsumptionMGO",
        "BoilerConsumptionHFO",
        "BoilerConsumptionMGO",
        "IGSConsumptionMGO",
        "IGSConsumptionHFO"
    ]

    # Ensure all fuel columns exist and are numeric
    for col in fuel_cols:
        if col in filtered.columns:
            filtered[col] = pd.to_numeric(filtered[col], errors='coerce').fillna(0)
        else:
            filtered[col] = 0

    total_fuel = round(filtered[fuel_cols].sum().sum(), 3)

    # Total CO2
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

    # Use provided DWT or detect from sheet
    if dwt == 0:
        if "DraftDisplacementActual" in filtered.columns and not filtered["DraftDisplacementActual"].empty:
            dwt = filtered["DraftDisplacementActual"].iloc[0]
        else:
            dwt = 50000  # fallback

    attained_aer = (co2 / (dwt * distance))*1000000 if distance > 0 else 0

    # Required AER
    required_aer = REQUIRED_AER_2025.get(ship_type, 7.0)

    # Annual rating
    if attained_aer <= 0.75 * required_aer:
        rating = "A"
    elif attained_aer <= 0.9 * required_aer:
        rating = "B"
    elif attained_aer <= required_aer:
        rating = "C"
    elif attained_aer <= 1.1 * required_aer:
        rating = "D"
    else:
        rating = "E"

    result = {
        "Total Distance (nm)": float(distance),
        "Total Fuel (MT)": float(total_fuel),
        "CO₂ Emission (MT)": float(co2),
        "Attained AER (g CO₂ / DWT-nm)": float(attained_aer),
        "Required AER 2025": required_aer,
        "CII Rating 2025": rating,
        "DWT Used (t)": float(dwt)
    }

    return filtered, result
