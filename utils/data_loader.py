import pandas as pd
import streamlit as st

def load_excel(file, sheet):
    try:
        df = pd.read_excel(file, sheet_name=sheet)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading sheet {sheet}: {e}")
        return pd.DataFrame()
