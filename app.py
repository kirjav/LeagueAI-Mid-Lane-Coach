import streamlit as st
import os
import pandas as pd
import sys

# Import core logic
sys.path.append(os.path.abspath("src"))
from analysis.full_analysis_pipeline import full_analysis_pipeline


st.set_page_config(page_title="League Lane Coach", layout="centered")

st.title("🎮 League Mid Lane Coach")
st.markdown("Analyze your lane phase and get feedback on how to improve.")

with st.form("lane_form"):
    summoner = st.text_input("Summoner Name (e.g. Wallaby#Rito)", "")
    server = st.selectbox("Server", ["NA1", "EUW1", "KR", "BR1", "EUN1", "JP1", "OC1", "RU", "TR1"])
    match_number = st.text_input("Match ID (numeric part only)", "")

    submitted = st.form_submit_button("Analyze My Match")

if submitted:
    if not summoner or not match_number:
        st.error("Please fill in all fields.")
    else:
        with st.spinner("Fetching and analyzing your match..."):
            try:
                result = full_analysis_pipeline(match_number, server, summoner)

                st.success("✅ Analysis Complete")
                st.markdown(f"### 🧠 Lane Score: **{result['lane_score']:.2f}**")

                st.markdown("### 📋 Feedback")
                for cat, items in result['feedback'].items():
                    st.markdown(f"**{cat}:**")
                    for item in items:
                        st.markdown(f"- {item}")

            except Exception as e:
                st.error(f"❌ Failed to analyze match: {e}")
