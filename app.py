import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import altair as alt

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

# --- 2. GET DATA ---
query = """
SELECT DISTINCT ON (web_name)
    web_name, team_name, position, cost, selected_by_percent, status,
    
    -- Activity
    minutes, starts, matches_played, total_points, points_per_game,
    
    -- Attack
    xg, xa, xgi, goals_scored, assists,
    
    -- Defense
    clean_sheets, goals_conceded, xgc,
    
    -- Work Rate
    def_cons, tackles, recoveries, cbi,
    
    -- Value
    form, value_season, bps
FROM human_readable_fpl
ORDER BY web_name, snapshot_time DESC
"""
df = pd.read_sql(query, engine)

# --- 3. CALCULATE METRICS ---
df = df.fillna(0)
df['matches_played'] = df['matches_played'].replace(0, 1)
df['minutes'] = df['minutes'].replace(0, 1)

# Metric Calculations
df['dc_per_match'] = df['def_cons'] / df['matches_played']
df['dc_per_90'] = (df['def_cons'] / df['minutes']) * 90
df['avg_minutes'] = df['minutes'] / df['matches_played']
df['tackles_per_90'] = (df['tackles'] / df['minutes']) * 90
df['xgc_per_90'] = (df['xgc'] / df['minutes']) * 90


# --- 4. SIDEBAR FILTERS ---
with st.sidebar:
    if "logo.png" in [f.name for f in os.scandir(".")]: 
        st.image("logo.png", width=200)
    
    st.header("🎯 Master Filters")

    # Position
    position = st.multiselect("Position", ["GKP", "DEF", "MID", "FWD"], default=["DEF", "MID", "FWD"])
    
    # Cost
    max_price = st.slider("Max Price (£)", 3.8, 15.1, 15.1, 0.1)
    
    # NEW: Ownership Filter
    max_owner = st.slider("Max Ownership (%)", 0.0, 100.0, 100.0, 0.5, help="Lower this to find Differentials!")

    st.subheader("⚙️ Reliability")
    min_avg_mins = st.slider("Avg Minutes per Match", 0, 90, 45)
    min_ppg = st.slider("Min Points Per Game", 0.0, 10.0, 2.5, 0.1)

    st.subheader("🛡️ Work Rate (Per 90)")
    min_dc90 = st.slider("Min Def. Contributions / 90", 0.0, 15.0, 0.0, 0.5)

# --- 5. FILTER DATA ---
filtered = df[
    (df['position'].isin(position)) &
    (df['cost'] <= max_price) &
    (df['selected_by_percent'] <= max_owner) &  # <--- NEW FILTER LOGIC
    (df['avg_minutes'] >= min_avg_mins) & 
    (df['points_per_game'] >= min_ppg) &
    (df['dc_per_90'] >= min_dc90)
]

# --- 6. DISPLAY ---
st.title(f"🚀 FPL Metric 2026 ({len(filtered)})")

# Top Level Metrics
col1, col2, col3, col4 = st.columns(4)
if not filtered.empty:
    best_xg = filtered.sort_values('xg', ascending=False).iloc[0]
    best_dc = filtered.sort_values('dc_per_90', ascending=False).iloc[0]
    best_val = filtered.sort_values('value_season', ascending=False).iloc[0]
    
    col1.metric("🔥 Threat King", best_xg['web_name'], f"{best_xg['xg']} xG")
    col2.metric("🛡️ Work Rate (DC/90)", best_dc['web_name'], f"{best_dc['dc_per_90']:.2f}")
    col3.metric("💰 Best Value", best_val['web_name'], f"{best_val['value_season']}")
    col4.metric("🧠 AVG Points", f"{filtered['points_per_game'].mean():.2f}", "PPG")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "⚔️ Attack", "🛡️ Defense", "⚙️ Work Rate (2026)"])

with tab1:
    st.dataframe(
        filtered[['web_name', 'team_name', 'position', 'cost', 'selected_by_percent', 'total_points', 'points_per_game', 'avg_minutes']].sort_values('total_points', ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "cost": st.column_config.NumberColumn("Price", format="£%.1f"),
            "selected_by_percent": st.column_config.NumberColumn("Own%", format="%.1f%%"), # <--- NEW COLUMN
            "points_per_game": st.column_config.NumberColumn("PPG", format="%.1f"),
            "avg_minutes": st.column_config.NumberColumn("Mins/Gm", format="%.0f"),
        }
    )

with tab2: 
    st.dataframe(
        filtered[['web_name', 'xg', 'xa', 'xgi', 'goals_scored']].sort_values('xg', ascending=False),
        use_container_width=True, hide_index=True,
        column_config={"xg": st.column_config.NumberColumn("xG", format="%.2f")}
    )

with tab3: 
    st.dataframe(
        filtered[['web_name', 'clean_sheets', 'xgc', 'xgc_per_90']].sort_values('clean_sheets', ascending=False),
        use_container_width=True, hide_index=True,
        column_config={"xgc_per_90": st.column_config.NumberColumn("xGC/90", format="%.2f")}
    )

with tab4: 
    st.dataframe(
        filtered[['web_name', 'dc_per_match', 'dc_per_90', 'tackles_per_90', 'def_cons']].sort_values('dc_per_90', ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "def_cons": st.column_config.NumberColumn("Total DC"),
            "dc_per_match": st.column_config.NumberColumn("DC/Match", format="%.1f"),
            "dc_per_90": st.column_config.NumberColumn("DC/90", format="%.2f"),
            "tackles_per_90": st.column_config.NumberColumn("Tackles/90", format="%.2f"),
        }
    )

# --- FOOTER ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        <p>📊 <strong>FPL Metric 2026</strong> | Built for the Fantasy Premier League Community</p>
    </div>
    """,
    unsafe_allow_html=True
)
