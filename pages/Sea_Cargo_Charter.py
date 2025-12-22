import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from utils.scc_utils import calculate_scc_intensity
from utils.operations import classify_operation_by_events_in_range
from utils.data_loader import load_excel
from utils.leg_utils import assign_legs, summarize_legs

from utils.unlocode_utils import map_ports

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="SCC Calculator", layout="wide")
st.markdown("<h2>🌍 SEA CARGO CHARTER – EMISSIONS INTENSITY TOOL</h2>", unsafe_allow_html=True)

# ==================================================
# FILE UPLOAD
# ==================================================
uploaded = st.file_uploader(
    "Upload Noon Report Excel (LogAbstract Sheet)",
    type=["xlsx"]
)

ship_type = st.selectbox(
    "Select Ship Type",
    [
        "Bulk Carrier",
        "Tanker",
        "Container",
        "RoRo",
        "General Cargo",
        "Cable Layer"
    ]
)

# ==================================================
# HELPERS
# ==================================================
def safe(v):
    return 0.0 if v is None or pd.isna(v) else float(v)


def autopct_with_values(values, unit=""):
    total = sum(values)

    def _autopct(pct):
        val = pct * total / 100.0
        return "" if val <= 0 else f"{val:.1f}{unit}\n({pct:.1f}%)"

    return _autopct


# ==================================================
# MAIN APP
# ==================================================
if uploaded:

    df = load_excel(uploaded, "LogAbstract")
    df = map_ports(df)
    if df.empty:
        st.error("❌ No data found in LogAbstract sheet.")
        st.stop()

    cargo_mt = st.number_input(
        "Enter Average Cargo Onboard (MT)",
        min_value=0.0,
        value=30000.0,
        step=500.0
    )

    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("From Date")
    with col2:
        date_to = st.date_input("To Date")

    # ==================================================
    # CALCULATE BUTTON
    # ==================================================
    if st.button("🚀 Calculate SCC Intensity"):

        # ---------------- SCC ----------------
        filtered, result = calculate_scc_intensity(
            df=df,
            ship_type=ship_type,
            date_from=date_from,
            date_to=date_to,
            cargo_mt=cargo_mt
        )

        st.success("✅ SCC Calculation Complete")

        # ==================================================
        # LEG-BASED OPERATIONAL DATA
        # ==================================================
        st.subheader("📄 Filtered Operational Data (By Voyage Legs)")

        legged_df = assign_legs(filtered)
        leg_summary = summarize_legs(legged_df)

        if leg_summary.empty:
            st.warning("No Departure / Arrival legs detected.")
        else:
            for _, row in leg_summary.iterrows():

                title = (
                    f"🛳 {row['Leg_ID']} | "
                    f"{row['From']} ➜ {row['To']} | "
                    f"{row['Distance (NM)']:.1f} NM | "
                    f"{row['Fuel (MT)']:.2f} MT"
                )

                with st.expander(title):
                    st.markdown(
                        f"""
                        **Start:** {row['Start']}  
                        **End:** {row['End']}  
                        **Records:** {row['Records']}
                        """
                    )

                    st.dataframe(
                        legged_df[legged_df["Leg_ID"] == row["Leg_ID"]],
                        use_container_width=True
                    )

        # ==================================================
        # SCC RESULTS
        # ==================================================
        st.subheader("📊 SCC Results")
        st.json(result)

        # ==================================================
        # OPERATIONS
        # ==================================================
        st.subheader("⚓ Operational Breakdown")

        ops = classify_operation_by_events_in_range(
            df, date_from, date_to
        )

        st.json(ops)

        # ==================================================
        # HOURS & FUEL
        # ==================================================
        sea_h = safe(ops.get("Sea Hours"))
        port_h = safe(ops.get("Port Hours"))
        drift_h = safe(ops.get("Drifting Hours"))

        total_hfo = (
            safe(ops.get("Sea HFO")) +
            safe(ops.get("Port HFO")) +
            safe(ops.get("Drifting HFO"))
        )

        total_mgo = (
            safe(ops.get("Sea MGO")) +
            safe(ops.get("Port MGO")) +
            safe(ops.get("Drifting MGO"))
        )

        # ==================================================
        # CHARTS
        # ==================================================
        st.subheader("📈 SCC Operational Distribution")

        c1, c2 = st.columns(2)

        with c1:
            fig1, ax1 = plt.subplots(figsize=(4, 4))
            ax1.pie(
                [sea_h, port_h, drift_h],
                labels=["Sea", "Port", "Drifting"],
                autopct=autopct_with_values([sea_h, port_h, drift_h], " h"),
                startangle=90
            )
            ax1.set_title("Hours Distribution")
            st.pyplot(fig1)

        with c2:
            fig2, ax2 = plt.subplots(figsize=(4, 4))
            ax2.pie(
                [total_hfo, total_mgo],
                labels=["HFO", "MGO"],
                autopct=autopct_with_values([total_hfo, total_mgo], " MT"),
                startangle=90
            )
            ax2.set_title("Fuel Split")
            st.pyplot(fig2)

else:
    st.info("⬆️ Upload an Excel file to begin SCC analysis.")
