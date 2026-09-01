import streamlit as st
from config import UNIVERSITY_CONFIG

st.set_page_config(page_title=UNIVERSITY_CONFIG['app_title'], layout="wide")
st.title(f"🏛️ {UNIVERSITY_CONFIG['app_title']}")
st.info(f"Initializing live portal for {UNIVERSITY_CONFIG['full_name']} [{UNIVERSITY_CONFIG['nirf_id']}]...")
