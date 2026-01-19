import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="FPL Metric", page_icon="⚽")

# --- 1. SETUP ---
try:
    url = st.secrets["DATABASE_URL"]
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(url)
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

# --- 2. SIDEBAR FILTERS ---
st.sidebar.header("🎯 Filters")
min_mins = st.sidebar.slider("Min Minutes (Last 48h)", 0, 90, 60)
max_price = st.sidebar.slider("Max Price (£)", 3.8, 14.0, 14.0, 0.1)
max_own = st.sidebar.slider("Max Ownership (%)", 0, 100, 10)
position = st.sidebar.multiselect("Position", ["GKP", "DEF", "MID", "FWD"], default=["DEF", "MID", "FWD"])

# --- 3. GET DATA ---
query = """
SELECT 
    web_name AS "Player", 
    team_name AS "Team", 
    position AS "Pos", 
    cost AS "Price", 
    selected_by_percent AS "Own%", 
    xg AS "xG", 
    minutes
FROM human_readable_fpl
WHERE snapshot_time > NOW() - INTERVAL '48 hours'
"""
df = pd.read_sql(query, engine)

# --- 4. FILTER DATA ---
filtered = df[
    (df['minutes'] >= min_mins) & 
    (df['Price'] <= max_price) & 
    (df['Own%'] <= max_own) &
    (df['Pos'].isin(position))
]

# --- 5. DISPLAY ---
st.title(f"💎 Hidden Gems ({len(filtered)})")

# Top 3 Cards
col1, col2, col3 = st.columns(3)
if not filtered.empty:
    best_xg = filtered.sort_values(by='xG', ascending=False).iloc[0]
    cheapest = filtered.sort_values(by='Price', ascending=True).iloc[0]
    
    col1.metric("Highest Threat", best_xg['Player'], f"{best_xg['xG']} xG")
    col2.metric("Best Value", cheapest['Player'], f"£{cheapest['Price']}m")

# Main Table
st.dataframe(
    filtered.sort_values(by='xG', ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Price": st.column_config.NumberColumn(format="£%.1fm"),
        "Own%": st.column_config.NumberColumn(format="%.1f%%"),
        "xG": st.column_config.NumberColumn(format="%.2f"),
    }
)
