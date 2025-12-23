import pandas as pd
from utils.unlocode_utils import resolve_port_name


# --------------------------------------------------
# STEP 1: ASSIGN LEG IDs
# --------------------------------------------------
def assign_legs(df):

    df = df.copy()
    df["DateTimeInUTC"] = pd.to_datetime(df["DateTimeInUTC"], errors="coerce")
    df = df.sort_values("DateTimeInUTC")

    leg_id = 0
    active_leg = False
    leg_ids = []

    for _, row in df.iterrows():
        event = str(row.get("EventType", "")).lower()

        if "departure" in event:
            leg_id += 1
            active_leg = True

        leg_ids.append(f"LEG-{leg_id}" if active_leg else None)

        if "arrival" in event and active_leg:
            active_leg = False

    df["Leg_ID"] = leg_ids
    return df


# --------------------------------------------------
# STEP 2: LEG SUMMARY
# --------------------------------------------------
def summarize_voyages(df):

    summaries = []

    for voyage_no, vdf in df.groupby("VoyageNumber", dropna=True):

        vdf = vdf.sort_values("DateTimeInUTC")

        from_code = vdf["VoyageFrom"].iloc[0] if "VoyageFrom" in vdf.columns else ""
        to_code = vdf["VoyageTo"].iloc[-1] if "VoyageTo" in vdf.columns else ""

        summaries.append({
            "VoyageNumber": voyage_no,
            "Total_Legs": vdf["Leg_ID"].nunique(),
            "From": f"{resolve_port_name(from_code)} ({from_code})",
            "To": f"{resolve_port_name(to_code)} ({to_code})",
            "Start": vdf["DateTimeInUTC"].min(),
            "End": vdf["DateTimeInUTC"].max(),
            "Total_Distance_NM": vdf["Distance"].fillna(0).sum(),
            "Total_Fuel_MT": vdf.filter(like="Consumption").fillna(0).sum().sum(),
            "Total_Records": len(vdf)
        })

    return pd.DataFrame(summaries)
