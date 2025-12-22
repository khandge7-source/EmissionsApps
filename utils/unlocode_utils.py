import pandas as pd

# --------------------------------------------------
# UN/LOCODE → PORT NAME MAP
# --------------------------------------------------
UNLOCODE_MAP = {
    "IDBLW": "Mumbai",
    "INNSA": "Nhava Sheva",
    "INMUN": "Mundra",
    "SGSIN": "Singapore",
    "CNSHA": "Shanghai",
    "NLRTM": "Rotterdam",
    "AEJEA": "Jebel Ali",
    "USLAX": "Los Angeles",
    "USNYC": "New York",
}

# --------------------------------------------------
# SINGLE VALUE RESOLVER
# --------------------------------------------------
def resolve_port_name(unlo_code: str) -> str:
    """
    Returns Port Name for UN/LOCODE.
    If not found, returns original UN/LOCODE.
    """
    if pd.isna(unlo_code):
        return ""

    code = str(unlo_code).strip().upper()
    return UNLOCODE_MAP.get(code, code)

# --------------------------------------------------
# DATAFRAME MAPPER (STEP 2)
# --------------------------------------------------
def map_ports(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds VoyageFromName and VoyageToName columns
    """

    df = df.copy()

    if "VoyageFrom" in df.columns:
        df["VoyageFromName"] = df["VoyageFrom"].apply(resolve_port_name)

    if "VoyageTo" in df.columns:
        df["VoyageToName"] = df["VoyageTo"].apply(resolve_port_name)

    return df
