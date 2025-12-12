import streamlit as st

def load_bootstrap():
    with open("assets/bootstrap.min.css", "r") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
