import pandas as pd

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
def summarize_legs(df):

    summaries = []

    for leg_id, g in df.groupby("Leg_ID", dropna=True):

        summaries.append({
            "Leg_ID": leg_id,
            "From": g["VoyageFrom"].iloc[0] if "VoyageFrom" in g.columns else "",
            "To": g["VoyageTo"].iloc[-1] if "VoyageTo" in g.columns else "",
            "Start": g["DateTimeInUTC"].min(),
            "End": g["DateTimeInUTC"].max(),
            "Distance (NM)": g["Distance"].fillna(0).sum(),
            "Fuel (MT)": g.filter(like="Consumption").fillna(0).sum().sum(),
            "Records": len(g)
        })

    return pd.DataFrame(summaries)
