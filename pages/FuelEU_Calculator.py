import streamlit as st
from utils.style_utils import load_bootstrap

st.set_page_config(page_title="FuelEU Calculator")
st.markdown(load_bootstrap(), unsafe_allow_html=True)

st.title("📕 FuelEU Calculator")
st.info("Feature under development.")
