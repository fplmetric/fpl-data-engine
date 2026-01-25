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
    
    /* DROPDOWN CURSOR FIX */
    div[data-baseweb="select"] > div {
        cursor: pointer !important;
    }
    
    /* CONTAINER 1: Player Table (Scrollable) */
    .player-table-container {
        max-height: 500px; 
        overflow-y: auto; 
        border: 1px solid #444;
        border-radius: 8px; 
        margin-bottom: 20px;
        position: relative;
        padding: 0; 
        background-color: #121212; 
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }

    /* CONTAINER 2: Fixture Ticker (Full View) */
    .fixture-table-container {
        width: 100%;
        border: 1px solid #444;
        border-radius: 8px;
        overflow-x: auto;
        padding: 0;
        background-color: #121212;
    }

    /* MODERN TABLE STYLING */
    .modern-table {
        width: 100%;
        border-collapse: separate; 
        border-spacing: 0;
        font-family: 'Source Sans Pro', sans-serif;
    }

    /* === VISUALLY APPEALING HEADERS === */
    .modern-table th {
        background: linear-gradient(to bottom, #5e0066, #37003c);
        color: #ffffff;
        padding: 16px 12px;
        text-align: center;
        font-weight: 700;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        text-shadow: 0 1px 2px rgba(0,0,0,0.4); 
        border-bottom: none;
        border-top: 1px solid rgba(255,255,255,0.1); 
        position: sticky;
        top: 0;
        z-index: 10;
        box-shadow: 0 5px 10px rgba(0,0,0,0.5); 
    }

    /* Corner Radius for Headers */
    .modern-table thead tr:first-child th:first-child { border-top-left-radius: 8px; }
    .modern-table thead tr:first-child th:last-child { border-top-right-radius: 8px; }

    .modern-table th:first-child, .modern-table th:nth-child(2) {
        text-align: left; 
        padding-left: 15px;
    }
    .modern-table td {
        padding: 12px 12px; 
        border-bottom: 1px solid #2c2c2c; 
        color: #E0E0E0;
        vertical-align: middle;
        font-size: 0.9rem;
        background-color: transparent !important; /* Allows row color to show */
        transition: background-color 0.2s ease; 
    }
    .modern-table tr:hover td {
        background-color: rgba(255, 255, 255, 0.07) !important; 
    }
    
    /* Badges & Pills */
    .pos-badge {
        background-color: #2a2a2a;
        color: #DDD;
        padding: 4px 10px;
        border-radius: 12px; 
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid #444;
    }
    .status-pill {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 5px rgba(0,0,0,0.5); 
    }
    
    /* Fixture Ticker Specifics */
    .diff-badge {
        display: block;
        padding: 8px 6px; 
        border-radius: 6px;
        text-align: center;
        font-weight: bold;
        font-size: 0.9rem; 
        width: 100%;
        box-shadow: inset 0 0 5px rgba(0,0,0,0.2); 
    }
    .fdr-legend {
        display: flex;
        gap: 15px;
        margin-top: 10px;
        font-family: sans-serif;
        font-size: 0.85rem;
        color: #B0B0B0;
        align-items: center;
    }
    .legend-item { display: flex; align-items: center; gap: 5px; }
    .legend-box {
        width: 25px; height: 25px; border-radius: 4px;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; color: black;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
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

@st.cache_data(ttl=3600)
def get_team_map():
    """Fetches mapping of Team Name -> Code for Logos"""
    static = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    t_map = {t['name']: t['code'] for t in static['teams']}
    
    # FIX: Handle Nottm Forest spelling mismatch manually
    if "Nott'm Forest" in t_map:
        t_map["Nottm Forest"] = t_map["Nott'm Forest"]
        
    return t_map

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
df = df[df['minutes'] >= 90]

filtered = df[
    (df['team_name'].isin(selected_teams)) &
    (df['position'].isin(position)) &
    (df['cost'] <= max_price) &
    (df['selected_by_percent'] <= max_owner) & 
    (df['avg_minutes'] >= min_avg_mins) & 
    (df['points_per_game'] >= min_ppg) &
    (df['dc_per_90'] >= min_dc90)
]

# --- FILTER LOGIC ---
if not show_unavailable:
    filtered = filtered[~filtered['status'].isin(['i', 'u', 'n', 's'])]

# --- 7. DISPLAY ---

# === NEW VISUALLY APPEALING TITLE ===
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(to right, #00FF85, #FFFFFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 255, 133, 0.3);
        margin: 0;
        padding-bottom: 10px;
    ">
        FPL Metric Scouting Dashboard
    </h1>
    <div style="width: 100px; height: 4px; background-color: #00FF85; margin: 0 auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- AESTHETIC FILTER HINT BANNER ---
st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, rgba(55,0,60,0.9) 0%, rgba(30,30,30,0.9) 100%);
        border: 1px solid #00FF85;
        border-radius: 8px;
        padding: 12px 20px;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 10px rgba(0, 255, 133, 0.1);
    ">
        <span style="font-size: 1.5rem; margin-right: 15px;">🔭</span>
        <span style="color: #E0E0E0; font-size: 1rem; font-family: 'Source Sans Pro', sans-serif; letter-spacing: 0.02em;">
            <strong style="color: #00FF85; text-transform: uppercase;">Scout's Tip:</strong> 
            Can't find a player? Open the <strong style="color: #fff; text-decoration: underline decoration-color: #00FF85;">Sidebar</strong> (top-left) to filter by Team, Position, and Price.
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(f"""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <span style="font-size: 1.2rem; color: #b0b0b0; margin-right: 15px;">
        Analyze live data, find differentials, and build your winning squad.
    </span>
    <span style="background-color: #00FF85; color: black; padding: 4px 12px; border-radius: 15px; font-weight: bold; font-size: 0.9rem; box-shadow: 0 0 10px rgba(0,255,133,0.4);">
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

# --------------------------------------------------------
# --- REUSABLE TABLE RENDERER FUNCTION ---
# --------------------------------------------------------
def render_modern_table(dataframe, column_config, sort_key):
    if dataframe.empty:
        st.info("No players match your filters.")
        return

    # --- SORTING LOGIC ---
    sort_options = {
        "total_points": "Total Points",
        "cost": "Price",
        "selected_by_percent": "Ownership",
        "matches_played": "Matches"
    }
    sort_options.update(column_config)
    
    if "news" in sort_options:
        del sort_options["news"]

    col_sort, _ = st.columns([1, 4])
    with col_sort:
        options_keys = list(sort_options.keys())
        options_labels = list(sort_options.values())
        selected_label = st.selectbox(f"Sort by:", options_labels, key=sort_key)
        selected_col = options_keys[options_labels.index(selected_label)]
        
    sorted_df = dataframe.sort_values(selected_col, ascending=False)
    team_map = get_team_map()
    
    # --- HEADER CONSTRUCTION ---
    base_headers = ["Name", "Team", "Pos", "Price", "Own%", "Matches"]
    dynamic_headers = list(column_config.values())
    all_headers = base_headers + dynamic_headers
    header_html = "".join([f"<th>{h}</th>" for h in all_headers])
    
    html_rows = ""
    for _, row in sorted_df.iterrows():
        row_style = ""
        text_color = "#E0E0E0"
        status_dot = '<span class="status-pill" style="background-color: #00FF85;"></span>'
        
        status = row['status']
        if status in ['i', 'u', 'n', 's']: 
            row_style = 'background-color: #4A0000;' 
            text_color = '#FFCCCC'
            status_dot = '<span class="status-pill" style="background-color: #FF0055;"></span>'
        elif status == 'd':
            row_style = 'background-color: #4A3F00;' 
            text_color = '#FFFFA0'
            status_dot = '<span class="status-pill" style="background-color: #FFCC00;"></span>'
            
        t_code = team_map.get(row['team_name'], 0)
        logo_img = f"https://resources.premierleague.com/premierleague/badges/20/t{t_code}.png"
        
        # --- FIXED METADATA CELLS ---
        html_rows += f"""<tr style="{row_style} color: {text_color};">"""
        html_rows += f"""<td style="font-weight: bold; font-size: 1rem; padding-left: 15px;">{status_dot} {row['web_name']}</td>"""
        html_rows += f"""<td style="display: flex; align-items: center; border-bottom: none; padding-left: 15px;"><img src="{logo_img}" style="width: 20px; margin-right: 8px;">{row['team_name']}</td>"""
        html_rows += f"""<td><span class="pos-badge">{row['position']}</span></td>"""
        
        s_price = "text-align: center; font-weight: bold; color: #00FF85;" if selected_col == 'cost' else "text-align: center;"
        html_rows += f"""<td style="{s_price}">£{row['cost']}</td>"""
        
        s_own = "text-align: center; font-weight: bold; color: #00FF85;" if selected_col == 'selected_by_percent' else "text-align: center;"
        html_rows += f"""<td style="{s_own}">{row['selected_by_percent']}%</td>"""
        
        s_match = "text-align: center; font-weight: bold; color: #00FF85;" if selected_col == 'matches_played' else "text-align: center;"
        html_rows += f"""<td style="{s_match}">{int(row['matches_played'])}</td>"""
        
        # --- DYNAMIC CELLS ---
        for col_name in column_config.keys():
            val = row[col_name]
            display_val = val
            if isinstance(val, float):
                display_val = f"{val:.2f}"
            if col_name in ['matches_played', 'avg_minutes', 'total_points', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded']:
                display_val = int(val)
            
            style = "text-align: center;"
            if col_name == selected_col:
                style += " font-weight: bold; color: #00FF85;"
                
            html_rows += f"""<td style="{style}">{display_val}</td>"""
        html_rows += "</tr>"

    html_table = f"""
    <div class="player-table-container">
        <table class="modern-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{html_rows}</tbody>
        </table>
    </div>
    """
    st.markdown(html_table, unsafe_allow_html=True)

# --------------------------------------------------------
# --- TABS LOGIC ---
# --------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "⚔️ Attack", "🛡️ Defense", "⚙️ Work Rate"])

with tab1:
    cols = { "points_per_game": "PPG", "avg_minutes": "Mins/Gm", "news": "News" }
    render_modern_table(filtered, cols, "sort_overview")

with tab2:
    cols = { "xg": "xG", "xa": "xA", "xgi": "xGI", "xgi_per_90": "xGI/90", "goals_scored": "Goals", "assists": "Assists" }
    render_modern_table(filtered, cols, "sort_attack")

with tab3:
    cols = { "clean_sheets": "Clean Sheets", "goals_conceded": "Conceded", "xgc": "xGC", "xgc_per_90": "xGC/90" }
    render_modern_table(filtered, cols, "sort_defense")

with tab4:
    cols = { "def_cons": "Total DC", "dc_per_90": "DC/90", "tackles": "Tackles", "tackles_per_90": "Tackles/90", "cbi": "CBI" }
    render_modern_table(filtered, cols, "sort_workrate")

# 4. FIXTURE TICKER
st.markdown("---") 
st.header("📅 Fixture Difficulty Ticker")

ticker_df = get_fixture_ticker()
gw_cols = [c for c in ticker_df.columns if c.startswith('GW')]
sort_options = ["Total Difficulty (Next 5)"] + gw_cols

col_ticker_sort, _ = st.columns([1, 4]) 
with col_ticker_sort:
    sort_choice = st.selectbox("Sort Table By:", sort_options)

if sort_choice == "Total Difficulty (Next 5)":
    ticker_df = ticker_df.sort_values('Total Difficulty', ascending=True)
else:
    target_dif_col = f"Dif_{sort_choice}"
    if target_dif_col in ticker_df.columns:
        ticker_df = ticker_df.sort_values(target_dif_col, ascending=True)

colors = {1: '#375523', 2: '#00FF85', 3: '#EBEBEB', 4: '#FF0055', 5: '#680808'}
text_colors = {1: 'white', 2: 'black', 3: 'black', 4: 'white', 5: 'white'}

html_rows = ""
for index, row in ticker_df.iterrows():
    team_cell = f'<td style="display: flex; align-items: center; border-bottom: 1px solid #333; padding-left: 15px;"><img src="{row["Logo"]}" style="width: 25px; margin-right: 12px; vertical-align: middle;"><span style="font-weight: bold; font-size: 1rem;">{row["Team"]}</span></td>'
    fixture_cells = ""
    for col in gw_cols:
        dif_key = f'Dif_{col}'
        difficulty = row.get(dif_key, 3)
        bg_color = colors.get(difficulty, '#EBEBEB')
        txt_color = text_colors.get(difficulty, 'black')
        fixture_cells += f'<td><span class="diff-badge" style="background-color: {bg_color}; color: {txt_color};">{row[col]}</span></td>'
    html_rows += f"<tr>{team_cell}{fixture_cells}</tr>"

header_cols = "".join([f"<th>{col}</th>" for col in gw_cols])
html_table = f"""
<div class="fixture-table-container">
<table class="modern-table">
  <thead><tr><th>Team</th>{header_cols}</tr></thead>
  <tbody>{html_rows}</tbody>
</table>
</div>
"""
st.markdown(html_table, unsafe_allow_html=True)

st.markdown("""
<div class="fdr-legend">
    <span style="font-weight:bold; color: white;">FDR Key:</span>
    <div class="legend-item">Easy <div class="legend-box" style="background-color: #375523; color: white;">1</div></div>
    <div class="legend-item"><div class="legend-box" style="background-color: #00FF85;">2</div></div>
    <div class="legend-item"><div class="legend-box" style="background-color: #EBEBEB;">3</div></div>
    <div class="legend-item"><div class="legend-box" style="background-color: #FF0055; color: white;">4</div></div>
    <div class="legend-item"><div class="legend-box" style="background-color: #680808; color: white;">5</div> Hard</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #B0B0B0;'>
        <p>📊 <strong>FPL Metric</strong> | Built for the Fantasy Premier League Community</p>
        <p><a href="https://x.com/FPL_Metric" target="_blank" style="color: #00FF85; text-decoration: none; font-weight: bold;">Follow us on X: @FPL_Metric</a></p>
    </div>
    """,
    unsafe_allow_html=True
)
