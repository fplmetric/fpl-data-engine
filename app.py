import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

st.set_page_config(page_title="FPL Metric 2026", page_icon="⚽", layout="wide")

# --- 1. SETUP ---
try:
    url = st.secrets["DATABASE_URL"]
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(url)
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

# --- 2. GET DATA (The "Data Vacuum" Query) ---
query = """
SELECT DISTINCT ON (web_name)
    web_name, team_name, position, cost, selected_by_percent, status,
    
    -- Activity
    minutes, starts, matches_played, total_points, points_per_game,
    
    -- Attack
    xg, xa, xgi, goals_scored, assists,
    
    -- Defense
    clean_sheets, goals_conceded, xgc,
    
    -- Work Rate (The New 2026 Suite)
    def_cons, tackles, recoveries, cbi,
    
    -- Value & Form
    form, value_form, value_season, bonus, bps, ict_index
FROM human_readable_fpl
ORDER BY web_name, snapshot_time DESC
"""
df = pd.read_sql(query, engine)

# --- 3. CALCULATE METRICS ---
df['matches_played'] = df['matches_played'].replace(0, np.nan)
df['minutes'] = df['minutes'].replace(0, np.nan)

# Per Match / Per 90 Stats
df['dc_per_match'] = df['def_cons'] / df['matches_played']
df['tackles_per_90'] = (df['tackles'] / df['minutes']) * 90
df['xgc_per_90'] = (df['xgc'] / df['minutes']) * 90

df = df.fillna(0)

# --- 4. SIDEBAR FILTERS ---
st.sidebar.header("🎯 Master Filters")
position = st.sidebar.multiselect("Position", ["GKP", "DEF", "MID", "FWD"], default=["DEF", "MID", "FWD"])
min_mins = st.sidebar.slider("Min Minutes Played", 0, 2000, 500, 100)
max_price = st.sidebar.slider("Max Price (£)", 3.8, 15.0, 15.0, 0.1)

st.sidebar.subheader("🛡️ Work Rate (New)")
min_dc = st.sidebar.slider("Min Def. Contributions (Total)", 0, 300, 0)
min_tackles = st.sidebar.slider("Min Tackles (Total)", 0, 100, 0)

# --- 5. FILTER DATA ---
filtered = df[
    (df['minutes'] >= min_mins) & 
    (df['cost'] <= max_price) & 
    (df['def_cons'] >= min_dc) &
    (df['tackles'] >= min_tackles) &
    (df['position'].isin(position))
]

# --- 6. DISPLAY ---
st.title(f"🚀 FPL Metric 2026 ({len(filtered)})")

# Top Level Metrics
col1, col2, col3, col4 = st.columns(4)
if not filtered.empty:
    best_xg = filtered.sort_values('xg', ascending=False).iloc[0]
    best_dc = filtered.sort_values('def_cons', ascending=False).iloc[0]
    col1.metric("🔥 Threat King", best_xg['web_name'], f"{best_xg['xg']} xG")
    col2.metric("🛡️ Workhorse (DC)", best_dc['web_name'], f"{int(best_dc['def_cons'])}")

# --- TABS FOR ORGANIZED DATA ---
tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "⚔️ Attack", "🛡️ Defense", "⚙️ Work Rate (2026)"])

with tab1:
    st.dataframe(filtered[['web_name', 'team_name', 'position', 'cost', 'total_points', 'form']].sort_values('total_points', ascending=False), use_container_width=True, hide_index=True)

with tab2: # Attack Tab
    st.dataframe(filtered[['web_name', 'xg', 'xa', 'xgi', 'goals_scored']].sort_values('xg', ascending=False), use_container_width=True, hide_index=True)

with tab3: # Defense Tab
    st.dataframe(filtered[['web_name', 'clean_sheets', 'xgc', 'xgc_per_90']].sort_values('clean_sheets', ascending=False), use_container_width=True, hide_index=True)

with tab4: # The New Work Rate Tab
    st.dataframe(
        filtered[['web_name', 'def_cons', 'dc_per_match', 'tackles', 'recoveries', 'cbi']].sort_values('def_cons', ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "def_cons": st.column_config.NumberColumn("Total DC", help="Defensive Contributions"),
            "dc_per_match": st.column_config.NumberColumn("DC/Match", format="%.1f"),
        }
    )
