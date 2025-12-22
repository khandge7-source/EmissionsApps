import pandas as pd

def classify_operation_by_events_in_range(df, date_from, date_to):

    df = df.copy()
    df["DateUTC"] = pd.to_datetime(df["DateUTC"], errors="coerce")

    date_from = pd.to_datetime(date_from)
    date_to = pd.to_datetime(date_to)

    df = df[(df["DateUTC"] >= date_from) & (df["DateUTC"] <= date_to)]

    def s(col):
        return df[col].fillna(0).sum() if col in df.columns else 0.0

    ops = {
        "Sea Hours": s("TimeElapsedSailing"),
        "Port Hours": (
            s("TimeElapsedLoadingUnloading") +
            s("TimeElapsedWaiting") +
            s("TimeElapsedAnchoring")
        ),
        "Drifting Hours": s("TimeElapsedDrifting"),

        "Sea HFO": s("MEConsumptionHFO"),
        "Sea MGO": s("MEConsumptionMGO"),

        "Port HFO": s("AEConsumptionHFO") + s("BoilerConsumptionHFO"),
        "Port MGO": s("AEConsumptionMGO") + s("BoilerConsumptionMGO"),

        "Drifting HFO": s("MEConsumptionHFO"),
        "Drifting MGO": s("MEConsumptionMGO"),
    }

    return ops
