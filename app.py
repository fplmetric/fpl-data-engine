import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import altair as alt
import os

# --- 1. SETUP ---
# CHANGED: page_icon is now your logo file
st.set_page_config(page_title="FPL Metric", page_icon="favicon.png", layout="wide")

# --- CUSTOM CSS FIX ---
# This forces the text inside the Green Multiselect Bars to be BLACK
st.markdown(
    """
    <style>
    /* Target the text inside the multiselect tags */
    span[data-baseweb="tag"] {
        color: black !important; /* Force black text */
        font-weight: bold;       /* Make it bold for better contrast */
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
SELECT DISTINCT ON (player_id)
    player_id, web_name, team_name, position, cost, selected_by_percent, status, news,
    
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
ORDER BY player_id, snapshot_time DESC
"""
df = pd.read_sql(query, engine)

# --- 3. CALCULATE METRICS ---
df = df.fillna(0)
df['matches_played'] = df['matches_played'].replace(0, 1)
df['minutes'] = df['minutes'].replace(0, 1)

# xGI per 90 Minutes
df['xgi_per_90'] = (df['xgi'] / df['minutes']) * 90

df['dc_per_match'] = df['def_cons'] / df['matches_played']
df['dc_per_90'] = (df['def_cons'] / df['minutes']) * 90
df['avg_minutes'] = df['minutes'] / df['matches_played']
df['tackles_per_90'] = (df['tackles'] / df['minutes']) * 90
df['xgc_per_90'] = (df['xgc'] / df['minutes']) * 90


# --- 4. STYLING FUNCTION ---
def highlight_status(row):
    status = row['status']
    # Darker red for unavailable
    if status in ['i', 'u', 'n', 's']:
        return ['background-color: #4A0000; color: #FFCCCC'] * len(row)
    # Darker yellow for doubtful
    elif status == 'd':
        return ['background-color: #4A3F00; color: #FFFFA0'] * len(row)
    else:
        return [''] * len(row)

# --- 5. SIDEBAR FILTERS ---
with st.sidebar:
    # CHANGED: Use columns to center the logo
    if "fpl_metric_logo.png" in [f.name for f in os.scandir(".")]: 
        col1, mid, col2 = st.columns([1, 2, 1]) # Create 3 columns
        with mid:
            st.image("fpl_metric_logo.png", use_container_width=True)
    
    st.header("🎯 Master Filters")

    # --- TEAM SELECTOR LOGIC ---
    all_teams = sorted(df['team_name'].unique())
    
    if 'team_selection' not in st.session_state:
        st.session_state['team_selection'] = all_teams

    def select_all_teams():
        st.session_state['team_selection'] = all_teams
    
    def deselect_all_teams():
        st.session_state['team_selection'] = []

    col_sel, col_desel = st.columns(2)
    with col_sel:
        st.button("✅ All", on_click=select_all_teams, use_container_width=True)
    with col_desel:
        st.button("❌ None", on_click=deselect_all_teams, use_container_width=True)

    selected_teams = st.multiselect(
        "Select Teams", 
        all_teams, 
        default=all_teams, 
        key='team_selection'
    )
    # ---------------------------

    position = st.multiselect("Position", ["GKP", "DEF", "MID", "FWD"], default=["DEF", "MID", "FWD"])
    max_price = st.slider("Max Price (£)", 3.8, 15.1, 15.1, 0.1)
    max_owner = st.slider("Max Ownership (%)", 0.0, 100.0, 100.0, 0.5)

    st.subheader("⚙️ Reliability")
    min_avg_mins = st.slider("Avg Minutes per Match", 0, 90, 0) 
    min_ppg = st.slider("Min Points Per Game", 0.0, 10.0, 0.0, 0.1)

    st.subheader("🛡️ Work Rate (Per 90)")
    min_dc90 = st.slider("Min Def. Contributions / 90", 0.0, 15.0, 0.0, 0.5)

    show_unavailable = st.checkbox("Show Unavailable Players (Red)", value=True)

# --- 6. FILTER DATA ---
filtered = df[
    (df['team_name'].isin(selected_teams)) &
    (df['position'].isin(position)) &
    (df['cost'] <= max_price) &
    (df['selected_by_percent'] <= max_owner) & 
    (df['avg_minutes'] >= min_avg_mins) & 
    (df['points_per_game'] >= min_ppg) &
    (df['dc_per_90'] >= min_dc90)
]

if not show_unavailable:
    filtered = filtered[filtered['status'] == 'a']

# --- 7. DISPLAY ---
st.title(f" FPL Metric ({len(filtered)})")

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
tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "⚔️ Attack", "🛡️ Defense", "⚙️ Work Rate "])

if not filtered.empty:
    styled_df = filtered.style.apply(highlight_status, axis=1)
else:
    styled_df = filtered

with tab1:
    st.dataframe(
        styled_df,
        use_container_width=True, 
        hide_index=True,
        column_order=['web_name', 'team_name', 'position', 'cost', 'selected_by_percent', 'news', 'total_points', 'points_per_game', 'avg_minutes'],
        column_config={
            "cost": st.column_config.NumberColumn("Price", format="£%.1f"),
            "selected_by_percent": st.column_config.NumberColumn("Own%", format="%.1f%%"),
            "points_per_game": st.column_config.NumberColumn("PPG", format="%.1f"),
            "avg_minutes": st.column_config.NumberColumn("Mins/Gm", format="%.0f"),
            "news": st.column_config.TextColumn("News", width="medium"), 
        }
    )

with tab2: 
    st.dataframe(
        styled_df,
        use_container_width=True, hide_index=True,
        column_order=['web_name', 'xg', 'xa', 'xgi', 'xgi_per_90', 'goals_scored'],
        column_config={
            "xg": st.column_config.NumberColumn("xG", format="%.2f"),
            "xgi_per_90": st.column_config.NumberColumn("xGI/90", format="%.2f")
        }
    )

with tab3: 
    st.dataframe(
        styled_df,
        use_container_width=True, hide_index=True,
        column_order=['web_name', 'clean_sheets', 'xgc', 'xgc_per_90'],
        column_config={"xgc_per_90": st.column_config.NumberColumn("xGC/90", format="%.2f")}
    )

with tab4: 
    st.dataframe(
        styled_df,
        use_container_width=True, hide_index=True,
        column_order=['web_name', 'dc_per_match', 'dc_per_90', 'tackles_per_90', 'def_cons'],
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
    <div style='text-align: center; color: #B0B0B0;'>
        <p>📊 <strong>FPL Metric</strong> | Built for the Fantasy Premier League Community</p>
    </div>
    """,
    unsafe_allow_html=True
)
