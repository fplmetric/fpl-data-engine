import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import altair as alt
import os
import requests

# --- 1. SETUP ---
st.set_page_config(page_title="FPL Metric", page_icon="favicon.png", layout="wide")

# --- CUSTOM CSS ---
st.markdown(
    """
    <style>
    /* Multiselect Tags */
    span[data-baseweb="tag"] {
        color: black !important;
        font-weight: bold;
    }
    
    /* Custom Fixture Table Styling */
    .fixture-table {
        width: 100%;
        border-collapse: collapse;
        font-family: sans-serif;
        font-size: 0.9rem;
    }
    .fixture-table th {
        background-color: #262730;
        color: #FFFFFF;
        padding: 12px;
        text-align: center;
        border-bottom: 2px solid #444;
    }
    .fixture-table th:first-child {
        text-align: left;
    }
    .fixture-table td {
        padding: 8px 12px;
        border-bottom: 1px solid #333;
        color: #E0E0E0;
        vertical-align: middle;
    }
    .fixture-table tr:hover {
        background-color: #2A2B35;
    }
    
    /* Difficulty Colors (Badges) */
    .diff-badge {
        display: block;
        padding: 6px 4px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        font-size: 0.85rem;
        width: 100%;
    }

    /* FDR Legend Styling */
    .fdr-legend {
        display: flex;
        gap: 15px;
        margin-top: 10px;
        font-family: sans-serif;
        font-size: 0.85rem;
        color: #B0B0B0;
        align-items: center;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .legend-box {
        width: 25px;
        height: 25px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: black; /* Default text color */
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

# --- FIXTURE TICKER LOGIC ---
@st.cache_data(ttl=3600) 
def get_fixture_ticker():
    static = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    teams = {
        t['id']: {
            'name': t['name'], 
            'short': t['short_name'],
            'code': t['code'] 
        } 
        for t in static['teams']
    }
    fixtures = requests.get('https://fantasy.premierleague.com/api/fixtures/?future=1').json()
    
    ticker_data = []
    
    for team_id, team_info in teams.items():
        team_fixtures = [f for f in fixtures if f['team_h'] == team_id or f['team_a'] == team_id][:5]
        logo_url = f"https://resources.premierleague.com/premierleague/badges/20/t{team_info['code']}.png"
        
        row = {
            'Logo': logo_url, 
            'Team': team_info['name'], 
            'Total Difficulty': 0 
        }
        
        for i, f in enumerate(team_fixtures):
            is_home = f['team_h'] == team_id
            opponent_id = f['team_a'] if is_home else f['team_h']
            difficulty = f['team_h_difficulty'] if is_home else f['team_a_difficulty']
            opponent_short = teams[opponent_id]['short']
            loc = "(H)" if is_home else "(A)"
            
            col_name = f"GW{f['event']}"
            row[col_name] = f"{opponent_short} {loc}"
            
            # Store difficulty data
            row['Total Difficulty'] += difficulty 
            row[f'Dif_{col_name}'] = difficulty 

        ticker_data.append(row)
        
    return pd.DataFrame(ticker_data)

# --- DATABASE QUERY ---
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
df['xgi_per_90'] = (df['xgi'] / df['minutes']) * 90
df['dc_per_match'] = df['def_cons'] / df['matches_played']
df['dc_per_90'] = (df['def_cons'] / df['minutes']) * 90
df['avg_minutes'] = df['minutes'] / df['matches_played']
df['tackles_per_90'] = (df['tackles'] / df['minutes']) * 90
df['xgc_per_90'] = (df['xgc'] / df['minutes']) * 90

# --- 4. STYLING FUNCTION ---
def highlight_status(row):
    status = row['status']
    if status in ['i', 'u', 'n', 's']:
        return ['background-color: #4A0000; color: #FFCCCC'] * len(row)
    elif status == 'd':
        return ['background-color: #4A3F00; color: #FFFFA0'] * len(row)
    else:
        return [''] * len(row)

# --- 5. SIDEBAR FILTERS ---
with st.sidebar:
    if "fpl_metric_logo.png" in [f.name for f in os.scandir(".")]: 
        col1, mid, col2 = st.columns([1, 5, 1]) 
        with mid:
            st.image("fpl_metric_logo.png", use_container_width=True)
    
    st.header("Filters")
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

    selected_teams = st.multiselect("Select Teams", all_teams, default=all_teams, key='team_selection')
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
st.title("FPL Metric Scouting Dashboard")
st.markdown(f"""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <span style="font-size: 1.2rem; color: #b0b0b0; margin-right: 15px;">
        Analyze live data, find differentials, and build your winning squad.
    </span>
    <span style="background-color: #00FF85; color: black; padding: 4px 12px; border-radius: 15px; font-weight: bold; font-size: 0.9rem;">
        {len(filtered)} Players Found
    </span>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
if not filtered.empty:
    best_xg = filtered.sort_values('xg', ascending=False).iloc[0]
    best_dc = filtered.sort_values('dc_per_90', ascending=False).iloc[0]
    best_val = filtered.sort_values('value_season', ascending=False).iloc[0]
    
    col1.metric("🔥 Threat King", best_xg['web_name'], f"{best_xg['xg']} xG")
    col2.metric("🛡️ Work Rate (DC/90)", best_dc['web_name'], f"{best_dc['dc_per_90']:.2f}")
    col3.metric("💰 Best Value", best_val['web_name'], f"{best_val['value_season']}")
    col4.metric("🧠 AVG Points", f"{filtered['points_per_game'].mean():.2f}", "PPG")

# 3. DATA TABLE
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

# 4. FIXTURE TICKER
st.markdown("---") 
st.header("📅 Fixture Difficulty Ticker")

ticker_df = get_fixture_ticker()

# --- SORT LOGIC ---
gw_cols = [c for c in ticker_df.columns if c.startswith('GW')]
sort_options = ["Total Difficulty (Next 5)"] + gw_cols
sort_choice = st.selectbox("Sort Table By:", sort_options)

if sort_choice == "Total Difficulty (Next 5)":
    ticker_df = ticker_df.sort_values('Total Difficulty', ascending=True)
else:
    target_dif_col = f"Dif_{sort_choice}"
    if target_dif_col in ticker_df.columns:
        ticker_df = ticker_df.sort_values(target_dif_col, ascending=True)

# --- HTML GENERATION ---
# 1. Colors Setup
colors = {
    1: '#375523', # Dark Green
    2: '#00FF85', # Green (Official Neon)
    3: '#EBEBEB', # Grey
    4: '#FF0055', # Pinkish Red
    5: '#680808'  # Dark Red
}
text_colors = {
    1: 'white',
    2: 'black',
    3: 'black',
    4: 'white',
    5: 'white'
}

# 2. Build Rows (No Indentation to fix Display Bug)
html_rows = ""
for index, row in ticker_df.iterrows():
    team_cell = f'<td style="display: flex; align-items: center; border-bottom: 1px solid #333;"><img src="{row["Logo"]}" style="width: 25px; margin-right: 12px; vertical-align: middle;"><span style="font-weight: bold; font-size: 1rem;">{row["Team"]}</span></td>'
    
    fixture_cells = ""
    for col in gw_cols:
        dif_key = f'Dif_{col}'
        difficulty = row.get(dif_key, 3)
        bg_color = colors.get(difficulty, '#EBEBEB')
        txt_color = text_colors.get(difficulty, 'black')
        fixture_cells += f'<td><span class="diff-badge" style="background-color: {bg_color}; color: {txt_color};">{row[col]}</span></td>'
    
    html_rows += f"<tr>{team_cell}{fixture_cells}</tr>"

# 3. Build Table Header
header_cols = "".join([f"<th>{col}</th>" for col in gw_cols])
html_table = f"""
<table class="fixture-table">
  <thead>
    <tr>
      <th>Team</th>
      {header_cols}
    </tr>
  </thead>
  <tbody>
    {html_rows}
  </tbody>
</table>
"""

st.markdown(html_table, unsafe_allow_html=True)

# 4. LEGEND (FDR Key)
st.markdown("""
<div class="fdr-legend">
    <span style="font-weight:bold; color: white;">FDR Key:</span>
    <div class="legend-item"><div class="legend-box" style="background-color: #375523; color: white;">1</div> Easy</div>
    <div class="legend-item"><div class="legend-box" style="background-color: #00FF85;">2</div></div>
    <div class="legend-item"><div class="legend-box" style="background-color: #EBEBEB;">3</div></div>
    <div class="legend-item"><div class="legend-box" style="background-color: #FF0055; color: white;">4</div></div>
    <div class="legend-item"><div class="legend-box" style="background-color: #680808; color: white;">5</div> Hard</div>
</div>
""", unsafe_allow_html=True)


# --- FOOTER ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #B0B0B0;'>
        <p>📊 <strong>FPL Metric</strong> | Built for the Fantasy Premier League Community</p>
        <p>
            <a href="https://x.com/FPL_Metric" target="_blank" style="color: #00FF85; text-decoration: none; font-weight: bold;">
                Follow us on X: @FPL_Metric
            </a>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
