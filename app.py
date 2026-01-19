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

# New Filter: Points Per Game
min_ppg = st.sidebar.slider("Min Points Per Game", 0.0, 10.0, 3.0, 0.1)

min_mins = st.sidebar.slider("Min Minutes (Last 48h)", 0, 90, 60)
max_price = st.sidebar.slider("Max Price (£)", 3.8, 14.0, 14.0, 0.1)
max_own = st.sidebar.slider("Max Ownership (%)", 0, 100, 15)
position = st.sidebar.multiselect("Position", ["GKP", "DEF", "MID", "FWD"], default=["DEF", "MID", "FWD"])

# --- 3. GET DATA (With DISTINCT ON to remove duplicates) ---
query = """
SELECT DISTINCT ON (web_name)
    web_name, 
    team_name, 
    position, 
    cost, 
    selected_by_percent, 
    xg, 
    minutes,
    points_per_game
FROM human_readable_fpl
ORDER BY web_name, snapshot_time DESC
"""
df = pd.read_sql(query, engine)

# --- 4. FILTER DATA ---
filtered = df[
    (df['minutes'] >= min_mins) & 
    (df['cost'] <= max_price) & 
    (df['selected_by_percent'] <= max_own) &
    (df['points_per_game'] >= min_ppg) &   # <--- New Filter Logic
    (df['position'].isin(position))
]

# Calculate Value Score (xG per Million)
filtered['value_score'] = (filtered['xg'] / filtered['cost']) * 10

# --- 5. DISPLAY ---
st.title(f"💎 Hidden Gems ({len(filtered)})")

# Top 3 Metrics
col1, col2, col3 = st.columns(3)
if not filtered.empty:
    best_xg = filtered.sort_values(by='xg', ascending=False).iloc[0]
    best_value = filtered.sort_values(by='value_score', ascending=False).iloc[0]
    
    col1.metric("Highest Threat", best_xg['web_name'], f"{best_xg['xg']} xG")
    col2.metric("Best Value (xG/£)", best_value['web_name'], f"£{best_value['cost']}m")

# Rename columns for the table
display_df = filtered.rename(columns={
    "web_name": "Player",
    "team_name": "Team",
    "position": "Pos",
    "cost": "Price",
    "selected_by_percent": "Own%", 
    "points_per_game": "PPG",       # <--- New Table Header
    "xg": "xG"
})

# Main Table
st.dataframe(
    display_df.sort_values(by='xG', ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Price": st.column_config.NumberColumn(format="£%.1fm"),
        "Own%": st.column_config.NumberColumn(format="%.1f%%"),
        "xG": st.column_config.NumberColumn(format="%.2f"),
        "PPG": st.column_config.NumberColumn(format="%.1f"), # Format PPG nicely
    }
)
