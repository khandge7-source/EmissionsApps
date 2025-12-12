import streamlit as st
from utils.style_utils import load_bootstrap

st.set_page_config(page_title="Monthly Emission Report")
st.markdown(load_bootstrap(), unsafe_allow_html=True)

st.title("📗 Monthly Emission Report")
st.info("Feature under development.")
