import pandas as pd

# --------------------------------------------------
# EMISSION FACTORS (kg CO2 / tonne fuel)
# --------------------------------------------------
EMISSION_FACTORS = {
    "HFO": 3114,
    "MGO": 3206,
    "MDO": 3206,
    "LFO": 3151,
    "LNG": 2750,
    "Methanol": 1375
}

# --------------------------------------------------
# SCC TRAJECTORY (Indicative – aligned with Sea Cargo Charter)
# gCO2 / tonne-nm
# --------------------------------------------------
SCC_TARGETS = {
    2023: 15.0,
    2030: 11.0,
    2040: 6.0,
    2050: 1.0
}


def interpolate_target(year):
    years = sorted(SCC_TARGETS.keys())
    for i in range(len(years) - 1):
        if years[i] <= year <= years[i + 1]:
            y1, y2 = years[i], years[i + 1]
            v1, v2 = SCC_TARGETS[y1], SCC_TARGETS[y2]
            return v1 + (v2 - v1) * (year - y1) / (y2 - y1)
    return SCC_TARGETS[years[-1]]


# --------------------------------------------------
# SCC + EEOI CALCULATION
# --------------------------------------------------
def calculate_scc_intensity(df, ship_type, date_from, date_to, cargo_mt):

    df["DateUTC"] = pd.to_datetime(df["DateUTC"], errors="coerce")
    filtered = df[(df["DateUTC"] >= pd.to_datetime(date_from)) &
                  (df["DateUTC"] <= pd.to_datetime(date_to))]

    if filtered.empty:
        return filtered, {}

    # ---------------- Distance ----------------
    distance_nm = filtered["Distance"].fillna(0).sum()

    # ---------------- Fuel ----------------
    fuel_map = {
        "HFO": filtered.filter(like="ConsumptionHFO").sum().sum(),
        "MGO": filtered.filter(like="ConsumptionMGO").sum().sum(),
        "MDO": filtered.filter(like="ConsumptionMDO").sum().sum(),
        "LFO": filtered.filter(like="ConsumptionLFO").sum().sum(),
        "LNG": filtered.filter(like="ConsumptionLNG").sum().sum(),
        "Methanol": filtered.filter(like="ConsumptionMethanol").sum().sum(),
    }

    # ---------------- CO2 ----------------
    total_co2_kg = sum(
        fuel * EMISSION_FACTORS.get(fuel_type, 0)
        for fuel_type, fuel in fuel_map.items()
    )

    # ---------------- SCC ----------------
    transport_work = cargo_mt * distance_nm
    scc_intensity = (total_co2_kg * 1000 / transport_work) if transport_work > 0 else 0

    # ---------------- EEOI ----------------
    eeoi = (total_co2_kg / transport_work) if transport_work > 0 else 0

    # ---------------- ALIGNMENT ----------------
    year = filtered["DateUTC"].dt.year.mode()[0]
    target = interpolate_target(year)
    alignment = "ALIGNED ✅" if scc_intensity <= target else "MISALIGNED ❌"

    result = {
        "Ship Type": ship_type,
        "Year": int(year),
        "Distance (NM)": round(distance_nm, 2),
        "Cargo (MT)": round(cargo_mt, 2),
        "Total CO2 (t)": round(total_co2_kg / 1000, 2),
        "SCC Intensity (gCO2/tonne-nm)": round(scc_intensity, 3),
        "EEOI (kgCO2/tonne-nm)": round(eeoi, 5),
        "SCC Target": round(target, 2),
        "Alignment": alignment
    }

    return filtered, result
