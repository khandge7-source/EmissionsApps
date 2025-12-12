import pandas as pd

# -------------------------------------
# CO₂ conversion factors per fuel type
# -------------------------------------
CII_FACTORS = {
    "HFO": 3.114,
    "MGO": 3.206,
    "LFO": 3.151,
    "LNG": 2.75,
}

# ----------------------------------------------------
# IMO Reference Line Parameters (G2 Guidelines)
# ----------------------------------------------------
REFERENCE_PARAMS = {
    "Bulk Carrier": (4745, 0.622),
    "Tanker": (5247, 0.610),
    "Container": (1984, 0.489),
    "General Cargo <20k": (588, 0.3885),
    "General Cargo ≥20k": (31948, 0.792),
    # Add more classes when needed
}

# ----------------------------------------------------
# IMO CII Reduction Factors (as % from 2019 reference)
# Expandable for future years
# ----------------------------------------------------
REDUCTION_FACTORS = {
    2023: 0.05,   # -5%
    2024: 0.07,   # -7%
    2025: 0.09,   # -9%
    2026: 0.11,   # -11% | Placeholder (update when IMO issues)
    2027: 0.13,   # Placeholder
    2028: 0.15,   # Placeholder
}

def calculate_cii(df, ship_type, date_from, date_to, dwt=0):
    # Convert dates
    df["DateUTC"] = pd.to_datetime(df["DateUTC"]).dt.date

    # Filter by date range
    filtered = df[(df["DateUTC"] >= date_from) & (df["DateUTC"] <= date_to)]

    # Total distance
    distance = filtered["Distance"].sum() if "Distance" in filtered.columns else 0

    # Total fuel calculations
    fuel_cols = [
        "MEConsumptionHFO", "MEConsumptionMGO",
        "AEConsumptionHFO", "AEConsumptionMGO",
        "BoilerConsumptionHFO", "BoilerConsumptionMGO",
        "IGSConsumptionHFO", "IGSConsumptionMGO"
    ]

    for col in fuel_cols:
        if col in filtered.columns:
            filtered[col] = pd.to_numeric(filtered[col], errors='coerce').fillna(0)
        else:
            filtered[col] = 0

    total_fuel = round(filtered[fuel_cols].sum().sum(), 3)

    # Total CO2 Emission
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

    # Detect or use provided DWT
    if dwt == 0:
        if "DraftDisplacementActual" in filtered.columns:
            dwt = filtered["DraftDisplacementActual"].iloc[0]
        else:
            dwt = 50000   # fallback

    # Avoid division by zero
    attained_aer = (co2 / (dwt * distance)) * 1_000_000 if distance > 0 else 0

    # ------------------------------------------
    # REQUIRED AER CALCULATION (dynamic by year)
    # ------------------------------------------

    # Determine year from date_to
    calculation_year = date_to.year
    reduction_factor = REDUCTION_FACTORS.get(calculation_year, 0.09)  # default 2025 value

    # Determine correct reference line parameters
    # For cable layer → use General Cargo <20k as proxy (recommended)
    if ship_type == "Cable Layer":
        a, c = REFERENCE_PARAMS["General Cargo <20k"]
    else:
        a, c = REFERENCE_PARAMS[ship_type]

    # Step 1: Reference line CII_REF
    cii_ref = a * (dwt ** (-c))

    # Step 2: Apply reduction
    required_aer_value = (1 - reduction_factor) * cii_ref

    # ------------------------------------------
    # CII RATING (A to E)
    # ------------------------------------------
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

    # Final result
        result = {
        "Year Evaluated": calculation_year,
        "Reduction Factor Applied": reduction_factor,
        "Total Distance (nm)": float(round(distance, 3)),
        "Total Fuel (MT)": float(round(total_fuel, 3)),
        "CO₂ Emission (MT)": float(round(co2, 3)),
        "Attained AER (g CO₂ / DWT-nm)": float(round(attained_aer, 3)),
        "Required AER": float(round(required_aer_value, 3)),
        "CII Rating": rating,
        "DWT Used": float(round(dwt, 3))
                        }


    return filtered, result
