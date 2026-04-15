import streamlit as st
import pandas as pd

st.set_page_config(page_title="Indonesia Flood Dashboard", layout="wide")
st.title("🌊 Indonesia Flood Pattern Analysis 2016–2025")
st.write("Dashboard loading...")

df = pd.read_excel("data/bencana_compiled_with_bps_shp.xlsx", sheet_name="Combined")
st.write(f"Records loaded: {len(df):,}")