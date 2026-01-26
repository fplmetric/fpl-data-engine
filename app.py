import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
import requests
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. SETUP ---
st.set_page_config(page_title="FPL Metric", page_icon="favicon.png", layout="wide")

# --- CUSTOM CSS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');
    
    /* GLOBAL */
    span[data-baseweb="tag"] { color: black !important; font-weight: bold; }
    div[data-baseweb="select"] > div { cursor: pointer !important; }
    
    /* TABS */
    div[data-baseweb="tab-list"] { gap: 8px; margin-bottom: 15px; }
    button[data-baseweb="tab"] {
        font-size: 1rem !important; font-weight: 600 !important; padding: 8px 20px !important;
        background-color: transparent !important; border-radius: 30px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important; color: #CCC !important; transition: all 0.3s ease;
    }
    button[data-baseweb="tab"]:hover {
        background-color: rgba(255, 255, 255, 0.05) !important; border-color: #FFF !important; color: #FFF !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #37003c !important; color: #00FF85 !important;
        border: 1px solid #00FF85 !important; box-shadow: 0 0 15px rgba(0, 255, 133, 0.15);
    }
    
    /* TABLES (Scrollable Fixed Height) */
    .player-table-container {
        /* Height for approx 10 rows */
        max-height: 550px; 
        overflow-y: auto; 
        overflow-x: auto;
        border: 1px solid #444; 
        border-radius: 8px; 
        margin-bottom: 20px; 
        background-color: transparent;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }
    .fixture-table-container {
        width: 100%;
        border: 1px solid #444; 
        border-radius: 8px; 
        overflow-x: auto; 
        margin-bottom: 20px; 
        background-color: transparent;
    }

    /* MODERN TABLE STYLE */
    .modern-table { width: 100%; border-collapse: separate; border-spacing: 0; font-family: 'Roboto', sans-serif; }
    .modern-table th {
        background: linear-gradient(to bottom, #5e0066, #37003c); color: #ffffff; padding: 16px 12px;
        text-align: center !important; font-weight: 700; font-size: 0.85rem; text-transform: uppercase;
        border-bottom: none; border-top: 1px solid rgba(255,255,255,0.1); position: sticky; top: 0; z-index: 10;
    }
    .modern-table th:first-child { text-align: left !important; padding-left: 20px !important; border-top-left-radius: 8px; }
    .modern-table th:last-child { border-top-right-radius: 8px; }
    .modern-table td {
        padding: 12px 12px; border-bottom: 1px solid #2c2c2c; color: #E0E0E0; vertical-align: middle; font-size: 0.9rem;
    }
    /* Note: Hover effect might be overridden by status colors, which is intended */
    .modern-table tr:hover td { background-color: rgba(255, 255, 255, 0.07); }
    
    .status-pill { display: inline-block; width: 8px; height: 8px; border-radius: 50%; box-shadow: 0 0 5px rgba(0,0,0,0.5); }
    .diff-badge { display: block; padding: 8px 6px; border-radius: 6px; text-align: center; font-weight: bold; font-size: 0.9rem; width: 100%; }
    .mini-fix-container { display: flex; gap: 4px; justify-content: center; }
    .mini-fix-box {
        width: 32px; height: 22px; display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem; font-weight: 800; border-radius: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }

    /* MATCH CARDS */
    .match-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
        gap: 15px; 
        margin-top: 15px; 
    }
    .match-card {
        background-color: rgba(255,255,255,0.03); 
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px; 
        padding: 15px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        transition: transform 0.2s, background-color 0.2s;
    }
    .match-card:hover { 
        background-color: rgba(255,255,255,0.08); 
        transform: translateY(-2px); 
        border-color: #00FF85; 
    }
    .team-col { display: flex; flex-direction: column; align-items: center; width: 80px; }
    .team-logo { width: 45px; height: 45px; object-fit: contain; margin-bottom: 8px; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.5)); }
    .team-name { font-size: 0.85rem; font-weight: 700; text-align: center; color: #FFF; line-height: 1.1; }
    .match-info { display: flex; flex-direction: column; align-items: center; color: #AAA; }
    .match-time { font-size: 1.1rem; font-weight: 700; color: #00FF85; margin-bottom: 2px; }
    .match-date { font-size: 0.75rem; text-transform: uppercase; }
    
    /* SCOUT TIP BOX */
    .scout-tip {
        background: linear-gradient(90deg, rgba(55,0,60,0.9) 0%, rgba(30,30,30,0.9) 100%);
        border: 1px solid #00FF85; border-radius: 8px; padding: 12px 20px;
        margin-bottom: 25px; display: flex; align-items: center;
        box-shadow: 0 4px 10px rgba(0, 255, 133, 0.1);
    }

    /* BMC BUTTON */
    .bmc-button {
        display: flex; align-items: center; justify-content: center; background-color: #FFDD00;
        color: #000000 !important; font-weight: 700; padding: 10px 20px; border-radius: 30px;
        margin-top: 20px; text-decoration: none; border: 2px solid #000; transition: transform 0.2s;
    }
    .bmc-button:hover { transform: translateY(-2px); text-decoration: none; }
    .bmc-logo { width: 20px; height: 20px; margin-right: 8px; }

    @media (max-width: 768px) { h1 { font-size: 1.8rem !important; } }
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

# --- 2. DATA FUNCTIONS ---

@st.cache_data(ttl=3600)
def get_team_map():
    static = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    t_map = {t['name']: t['code'] for t in static['teams']}
    if "Nott'm Forest" in t_map:
        t_map["Nottm Forest"] = t_map["Nott'm Forest"]
    return t_map

@st.cache_data(ttl=3600)
def get_expected_points_map():
    static = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    ep_map = {}
    for p in static['elements']:
        try:
            ep_map[p['id']] = float(p.get('ep_next', 0))
        except:
            ep_map[p['id']] = 0.0
    return ep_map

@st.cache_data(ttl=3600)
def get_next_gw_data():
    static = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    next_event = next((e for e in static['events'] if e['is_next']), None)
    if not next_event: return None, None, []
        
    gw_name = next_event['name']
    deadline_iso = next_event['deadline_time']
    teams = {t['id']: {'name': t['short_name'], 'code': t['code']} for t in static['teams']}
    fixtures = requests.get(f'https://fantasy.premierleague.com/api/fixtures/?event={next_event["id"]}').json()
    
    processed_fixtures = []
    for f in fixtures:
        home_t = teams.get(f['team_h'])
        away_t = teams.get(f['team_a'])
        dt_obj = datetime.strptime(f['kickoff_time'], "%Y-%m-%dT%H:%M:%SZ")
        processed_fixtures.append({
            'home_name': home_t['name'], 'home_code': home_t['code'],
            'away_name': away_t['name'], 'away_code': away_t['code'],
            'time': dt_obj.strftime("%H:%M"), 'date': dt_obj.strftime("%a %d %b")
        })
    return gw_name, deadline_iso, processed_fixtures

@st.cache_data(ttl=3600)
def get_next_gameweek_id():
    fixtures = requests.get('https://fantasy.premierleague.com/api/fixtures/?future=1').json()
    if fixtures: return fixtures[0]['event']
    return 38 

# --- 3. FIXTURE TICKER LOGIC ---
@st.cache_data(ttl=3600) 
def get_fixture_ticker(start_gw, end_gw):
    static = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    teams = {
        t['id']: {
            'name': t['name'], 'short': t['short_name'], 'code': t['code'],
            'str_att_h': t['strength_attack_home'], 'str_att_a': t['strength_attack_away'],
            'str_def_h': t['strength_defence_home'], 'str_def_a': t['strength_defence_away']
        } for t in static['teams']
    }
    fixtures = requests.get('https://fantasy.premierleague.com/api/fixtures/?future=1').json()
    ticker_data = []
    
    for team_id, team_info in teams.items():
        team_fixtures = [
            f for f in fixtures 
            if (f['team_h'] == team_id or f['team_a'] == team_id) and 
               (f['event'] >= start_gw and f['event'] <= end_gw)
        ]
        logo_url = f"https://resources.premierleague.com/premierleague/badges/50/t{team_info['code']}.png"
        row = {'Logo': logo_url, 'Team': team_info['name'], 'Diff_Overall': 0, 'Diff_Attack': 0, 'Diff_Defence': 0}
        
        for f in team_fixtures:
            is_home = f['team_h'] == team_id
            opponent_id = f['team_a'] if is_home else f['team_h']
            difficulty = f['team_h_difficulty'] if is_home else f['team_a_difficulty']
            opp_stats = teams[opponent_id]
            
            if is_home:
                opp_def = opp_stats['str_def_a']; opp_att = opp_stats['str_att_a']
            else:
                opp_def = opp_stats['str_def_h']; opp_att = opp_stats['str_att_h']
            
            col_name = f"GW{f['event']}"
            loc = "(H)" if is_home else "(A)"
            row[col_name] = f"{opp_stats['short']} {loc}"
            row['Diff_Overall'] += difficulty
            row['Diff_Attack'] += opp_def
            row['Diff_Defence'] += opp_att
            row[f'Dif_{col_name}'] = difficulty 

        ticker_data.append(row)
    return pd.DataFrame(ticker_data)

@st.cache_data(ttl=3600)
def get_team_upcoming_fixtures():
    static = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    fixtures = requests.get('https://fantasy.premierleague.com/api/fixtures/?future=1').json()
    teams_info = {t['id']: {'name': t['name'], 'short': t['short_name']} for t in static['teams']}
    team_fixtures_map = {}
    for team_id, info in teams_info.items():
        my_fixtures = [f for f in fixtures if f['team_h'] == team_id or f['team_a'] == team_id][:5]
        fixture_list = []
        for f in my_fixtures:
            is_home = f['team_h'] == team_id
            opponent_id = f['team_a'] if is_home else f['team_h']
            difficulty = f['team_h_difficulty'] if is_home else f['team_a_difficulty']
            opp_short = teams_info[opponent_id]['short']
            fixture_list.append({'opp': opp_short, 'diff': difficulty})
        team_fixtures_map[info['name']] = fixture_list
        if info['name'] == "Nott'm Forest": team_fixtures_map["Nottm Forest"] = fixture_list
    return team_fixtures_map

def get_db_price_changes():
    sql = """
    WITH Ranked AS (
        SELECT player_id, web_name, team_name, position, cost, selected_by_percent,
        ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY snapshot_time DESC) as rn
        FROM human_readable_fpl
    )
    SELECT * FROM Ranked WHERE rn <= 2;
    """
    try:
        df_hist = pd.read_sql(sql, engine)
        if df_hist.empty: return pd.DataFrame()
        df_latest = df_hist[df_hist['rn'] == 1].set_index('player_id')
        df_prev = df_hist[df_hist['rn'] == 2].set_index('player_id')
        merged = df_latest.join(df_prev, lsuffix='_now', rsuffix='_old')
        merged['change'] = merged['cost_now'] - merged['cost_old']
        movers = merged[merged['change'] != 0].copy()
        clean_movers = []
        for pid, row in movers.iterrows():
            clean_movers.append({
                'web_name': row['web_name_now'], 'team': row['team_name_now'], 'position': row['position_now'],
                'cost': row['cost_now'], 'change': row['change'], 'selected_by_percent': row['selected_by_percent_now']
            })
        return pd.DataFrame(clean_movers)
    except Exception as e:
        return pd.DataFrame()

# --- FETCH MAIN DATA ---
query = """
SELECT DISTINCT ON (player_id)
    player_id, web_name, team_name, position, cost, selected_by_percent, status, news,
    minutes, starts, matches_played, total_points, points_per_game,
    xg, xa, xgi, goals_scored, assists, clean_sheets, goals_conceded, xgc,
    def_cons, tackles, recoveries, cbi, form, value_season, bps
FROM human_readable_fpl ORDER BY player_id, snapshot_time DESC
"""
df = pd.read_sql(query, engine)
df = df.fillna(0)

# Calculate Metrics
df['matches_played'] = df['matches_played'].replace(0, 1)
df['minutes'] = df['minutes'].replace(0, 1)
df['avg_minutes'] = df['minutes'] / df['matches_played']
df['xgi_per_90'] = (df['xgi'] / df['minutes']) * 90
df['xgc_per_90'] = (df['xgc'] / df['minutes']) * 90
df['dc_per_90'] = (df['def_cons'] / df['minutes']) * 90
df['tackles_per_90'] = (df['tackles'] / df['minutes']) * 90

ep_map = get_expected_points_map()
df['ep_next'] = df['player_id'].map(ep_map).fillna(0.0)

# --- SIDEBAR ---
with st.sidebar:
    if "fpl_metric_logo.png" in [f.name for f in os.scandir(".")]: 
        col1, mid, col2 = st.columns([1, 5, 1]) 
        with mid: st.image("fpl_metric_logo.png", use_container_width=True)
    
    st.header("Filters")
    all_teams = sorted(df['team_name'].unique())
    if 'team_selection' not in st.session_state: st.session_state['team_selection'] = all_teams
    def select_all_teams(): st.session_state['team_selection'] = all_teams
    def deselect_all_teams(): st.session_state['team_selection'] = []
    
    col_sel, col_desel = st.columns(2)
    with col_sel: st.button("✅ All Teams", on_click=select_all_teams, use_container_width=True)
    with col_desel: st.button("❌ Clear Teams", on_click=deselect_all_teams, use_container_width=True)
    
    with st.form("filter_form"):
        st.caption("Adjust filters and click 'Apply'.")
        selected_teams = st.multiselect("Teams", all_teams, default=all_teams, key='team_selection')
        position = st.multiselect("Position", ["GKP", "DEF", "MID", "FWD"], default=["DEF", "MID", "FWD"])
        max_price = st.slider("Max Price (£)", 3.8, 15.1, 15.1, 0.1)
        max_owner = st.slider("Max Ownership (%)", 0.0, 100.0, 100.0, 0.5)
        submitted = st.form_submit_button("Apply Filters", use_container_width=True)

    st.markdown("---")
    st.markdown("""<a href="https://www.buymeacoffee.com/fplmetric" target="_blank" class="bmc-button"><img src="https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg" alt="Buy me a coffee" class="bmc-logo"><span>Buy me a coffee</span></a>""", unsafe_allow_html=True)

# --- FILTER LOGIC ---
df = df[df['minutes'] >= 90]
filtered = df[
    (df['team_name'].isin(selected_teams)) & (df['position'].isin(position)) &
    (df['cost'] <= max_price) & (df['selected_by_percent'] <= max_owner)
]

# --- MAIN DISPLAY ---
if "fpl_metric_logo.png" in [f.name for f in os.scandir(".")]: 
    _, col_main_logo, _ = st.columns([3, 2, 3]) 
    with col_main_logo: st.image("fpl_metric_logo.png", use_container_width=True)

st.markdown("""<div style="text-align: center; margin-bottom: 20px;"><h1 style="font-size: 3rem; font-weight: 900; background: linear-gradient(to right, #00FF85, #FFFFFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">FPL Metric</h1><div style="width: 80px; height: 4px; background-color: #00FF85; margin: 0 auto; border-radius: 2px;"></div></div>""", unsafe_allow_html=True)

# =========================================================================
# 📅 1. DEADLINE COUNTDOWN & FIXTURES (ENHANCED)
# =========================================================================
gw_name, deadline_iso, fixtures_data = get_next_gw_data()

if gw_name and deadline_iso:
    countdown_html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');
        .deadline-box {{
            background: linear-gradient(135deg, #1a001e 0%, #37003c 100%);
            border: 1px solid #00FF85; border-radius: 12px; padding: 15px;
            text-align: center; font-family: 'Roboto', sans-serif; color: white;
            box-shadow: 0 4px 15px rgba(0, 255, 133, 0.2); margin: 5px;
        }}
        .label {{ color: #00FF85; font-size: 0.9rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px; }}
        .timer {{ font-size: 2.2rem; font-weight: 900; margin: 0; line-height: 1.1; }}
        .sub {{ font-size: 0.85rem; color: #BBB; margin-top: 5px; }}
    </style>
    <div class="deadline-box">
        <div class="label">{gw_name} DEADLINE</div>
        <div id="timer" class="timer">Loading...</div>
        <div id="sub" class="sub"></div>
    </div>
    <script>
        var deadline = new Date("{deadline_iso}").getTime();
        var dateOpts = {{ weekday: 'long', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }};
        var readable = new Date("{deadline_iso}").toLocaleDateString('en-GB', dateOpts);
        document.getElementById("sub").innerText = readable + " (Local)";
        
        var x = setInterval(function() {{
            var now = new Date().getTime();
            var t = deadline - now;
            if (t < 0) {{
                clearInterval(x);
                document.getElementById("timer").innerHTML = "DEADLINE PASSED";
                document.getElementById("timer").style.color = "#FF0055";
            }} else {{
                var d = Math.floor(t / (1000 * 60 * 60 * 24));
                var h = Math.floor((t % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                var m = Math.floor((t % (1000 * 60 * 60)) / (1000 * 60));
                var s = Math.floor((t % (1000 * 60)) / 1000);
                document.getElementById("timer").innerHTML = d + "d " + h + "h " + m + "m " + s + "s ";
            }}
        }}, 1000);
    </script>
    """
    components.html(countdown_html, height=150)

    with st.expander(f"🏟️ View {gw_name} Fixtures (Kickoff Times)", expanded=False):
        if fixtures_data:
            cards_html = '<div class="match-grid">'
            for f in fixtures_data:
                h_img = f"https://resources.premierleague.com/premierleague/badges/50/t{f['home_code']}.png"
                a_img = f"https://resources.premierleague.com/premierleague/badges/50/t{f['away_code']}.png"
                cards_html += f"""
<div class="match-card">
    <div class="team-col"><img src="{h_img}" class="team-logo"><span class="team-name">{f['home_name']}</span></div>
    <div class="match-info"><span class="match-time">{f['time']}</span><span class="match-date">{f['date']}</span></div>
    <div class="team-col"><img src="{a_img}" class="team-logo"><span class="team-name">{f['away_name']}</span></div>
</div>"""
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)
        else:
            st.info("No fixtures found for next Gameweek.")

# =========================================================================

# --- INFO BOX ---
st.markdown(
    """
    <div class="scout-tip">
        <span style="color: #E0E0E0; font-size: 1rem; font-family: 'Roboto', sans-serif;">
            <strong style="color: #00FF85;">SCOUT'S TIP:</strong> 
            Can't find a player? Open the <strong style="color: #fff; text-decoration: underline decoration-color: #00FF85;">Sidebar</strong> to filter by Team, Position, and Price.
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)
if not filtered.empty:
    best_xgi = filtered.sort_values('xgi', ascending=False).iloc[0]
    best_dc = filtered.sort_values('dc_per_90', ascending=False).iloc[0]
    best_val = filtered.sort_values('value_season', ascending=False).iloc[0]
    best_ppg = filtered.sort_values('points_per_game', ascending=False).iloc[0]
    col1.metric("Threat King (xGI)", best_xgi['web_name'], f"{best_xgi['xgi']}")
    col2.metric("Work Rate (DC/90)", best_dc['web_name'], f"{best_dc['dc_per_90']:.2f}")
    col3.metric("Best Value", best_val['web_name'], f"{best_val['value_season']}")
    col4.metric("Best PPG", best_ppg['web_name'], f"{best_ppg['points_per_game']}")

def render_modern_table(dataframe, column_config, sort_key):
    if dataframe.empty:
        st.info("No players match your filters.")
        return

    sort_options = {"cost": "Price", "selected_by_percent": "Ownership", "matches_played": "Matches"}
    sort_options.update(column_config)
    if "news" in sort_options: del sort_options["news"]

    col_sort, _ = st.columns([1, 4])
    with col_sort:
        options_keys = list(sort_options.keys())
        options_labels = list(sort_options.values())
        selected_label = st.selectbox(f"Sort by:", options_labels, key=sort_key)
        selected_col = options_keys[options_labels.index(selected_label)]
        
    sorted_df = dataframe.sort_values(selected_col, ascending=False).head(100)
    team_map = get_team_map()
    team_fixtures = get_team_upcoming_fixtures()
    
    base_headers = ["Player", "Next 5", "Price", "Own%", "Matches"]
    dynamic_headers = list(column_config.values())
    all_headers = base_headers + dynamic_headers
    header_html = "".join([f"<th>{h}</th>" for h in all_headers])
    
    fdr_colors = {1: '#375523', 2: '#00FF85', 3: '#EBEBEB', 4: '#FF0055', 5: '#680808'}
    fdr_text = {1: 'white', 2: 'black', 3: 'black', 4: 'white', 5: 'white'}
    
    html_rows = ""
    for _, row in sorted_df.iterrows():
        t_code = team_map.get(row['team_name'], 0)
        logo_img = f"https://resources.premierleague.com/premierleague/badges/20/t{t_code}.png"
        
        # --- HIGHLIGHTING LOGIC ---
        status = row['status']
        row_style = ""
        if status in ['i', 'u', 'n', 's']: 
            row_style = 'background-color: rgba(74, 0, 0, 0.6);' # Red tint for injured
        elif status == 'd': 
            row_style = 'background-color: rgba(74, 63, 0, 0.6);' # Yellow tint for doubtful
            
        status_dot = '<span class="status-pill" style="background-color: #00FF85;"></span>'
        if status in ['i', 'u', 'n', 's']: status_dot = '<span class="status-pill" style="background-color: #FF0055;"></span>'
        elif status == 'd': status_dot = '<span class="status-pill" style="background-color: #FFCC00;"></span>'
        
        # Player Cell
        html_rows += f"""<tr style="{row_style}">
        <td style="padding-left: 20px;"><div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 10px;">{status_dot}</div><img src="{logo_img}" style="width: 35px;">
            <div style="display: flex; flex-direction: column;"><span style="font-weight: bold; color: #FFF;">{row['web_name']}</span><span style="font-size: 0.8rem; color: #AAA;">{row['team_name']} | {row['position']}</span></div>
        </div></td>"""
        
        # Fixtures Cell
        my_fixtures = team_fixtures.get(row['team_name'], [])
        fix_html = '<div class="mini-fix-container">'
        for f in my_fixtures:
            bg, txt = fdr_colors.get(f['diff'], '#333'), fdr_text.get(f['diff'], 'white')
            fix_html += f'<div class="mini-fix-box" style="background-color: {bg}; color: {txt};">{f["opp"]}</div>'
        fix_html += '</div>'
        html_rows += f'<td style="text-align: center;">{fix_html}</td>'
        
        # Dynamic Columns
        for col_name in ['cost', 'selected_by_percent', 'matches_played'] + list(column_config.keys()):
            val = row[col_name]
            if isinstance(val, float): val = f"{val:.2f}"
            
            # --- PRICE FORMAT FIX (1 decimal) ---
            if col_name == 'cost': val = f"£{float(val):.1f}"
            
            elif col_name == 'selected_by_percent': val = f"{val}%"
            elif col_name in ['matches_played', 'avg_minutes', 'total_points', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded']: val = int(float(val))
            
            style = "text-align: center;"
            if col_name == selected_col: style += " font-weight: bold; color: #00FF85;"
            html_rows += f"""<td style="{style}">{val}</td>"""
        html_rows += "</tr>"

    st.markdown(f"""<div class="player-table-container"><table class="modern-table"><thead><tr>{header_html}</tr></thead><tbody>{html_rows}</tbody></table></div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Attack", "Defense", "Work Rate"])
# --- NEWS COLUMN RESTORED IN TAB 1 ---
with tab1: render_modern_table(filtered, { "ep_next": "XP", "total_points": "Pts", "points_per_game": "PPG", "avg_minutes": "Mins/Gm", "news": "News" }, "sort_ov")
with tab2: render_modern_table(filtered, { "xg": "xG", "xa": "xA", "xgi": "xGI", "xgi_per_90": "xGI/90", "goals_scored": "Goals", "assists": "Assists" }, "sort_att")
with tab3: render_modern_table(filtered, { "clean_sheets": "Clean Sheets", "goals_conceded": "Conceded", "xgc": "xGC", "xgc_per_90": "xGC/90" }, "sort_def")
with tab4: render_modern_table(filtered, { "def_cons": "Total DC", "dc_per_90": "DC/90", "tackles": "Tackles", "tackles_per_90": "Tackles/90", "cbi": "CBI" }, "sort_wr")

st.markdown("---") 
st.header("Fixture Difficulty Ticker")
current_next_gw = get_next_gameweek_id()
horizon_opts = ["Next 3 GWs", "Next 5 GWs"] + [f"GW {current_next_gw+i}" for i in range(5)]
c1, c2, c3 = st.columns(3)
with c1: s_order = st.selectbox("Sort Order", ["Easiest", "Hardest", "Alphabetical"])
with c2: v_type = st.selectbox("Type", ["Overall", "Attack", "Defence"])
with c3: horizon = st.selectbox("Horizon", horizon_opts)

if horizon == "Next 3 GWs": s_gw, e_gw = current_next_gw, current_next_gw + 2
elif horizon == "Next 5 GWs": s_gw, e_gw = current_next_gw, current_next_gw + 4
else: s_gw = e_gw = int(horizon.split(" ")[1])

t_df = get_fixture_ticker(s_gw, e_gw)
if s_order == "Alphabetical": t_df = t_df.sort_values('Team')
else:
    s_col = "Diff_Attack" if v_type == "Attack" else "Diff_Defence" if v_type == "Defence" else "Diff_Overall"
    t_df = t_df.sort_values(s_col, ascending=(s_order == "Easiest"))

gw_cols = [c for c in t_df.columns if c.startswith('GW')]
h_rows = ""
for i, r in t_df.iterrows():
    f_cells = ""
    for c in gw_cols:
        d = r.get(f'Dif_{c}', 3)
        bg, txt = {1:'#375523', 2:'#00FF85', 3:'#EBEBEB', 4:'#FF0055', 5:'#680808'}.get(d, '#EBEBEB'), 'white' if d in [1,4,5] else 'black'
        f_cells += f'<td><span class="diff-badge" style="background-color: {bg}; color: {txt};">{r[c]}</span></td>'
    h_rows += f"""<tr><td style="padding-left: 15px; display: flex; align-items: center;"><img src="{r['Logo']}" style="width: 25px; margin-right: 10px;"><b>{r['Team']}</b></td>{f_cells}</tr>"""
st.markdown(f"""<div class="fixture-table-container"><table class="modern-table"><thead><tr><th>Team</th>{"".join([f"<th>{c}</th>" for c in gw_cols])}</tr></thead><tbody>{h_rows}</tbody></table></div>""", unsafe_allow_html=True)

st.markdown("---")
st.header("Market Movers (Daily Change)")
st.caption("Price changes over the last 24h.")
df_c = get_db_price_changes()
if df_c.empty: st.info("No price changes detected.")
else:
    c_r, c_f = st.columns(2)
    # --- ARROW FIX: VISIBLE COLORS ---
    icon_up = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#00FF85" stroke-width="4"><path d="M18 15l-6-6-6 6"/></svg>'
    icon_dn = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#FF0055" stroke-width="4"><path d="M6 9l6 6 6-6"/></svg>'
    
    with c_r:
        st.subheader("Price Risers")
        risers = df_c[df_c['change'] > 0].sort_values('change', ascending=False)
        if risers.empty: st.info("No risers.")
        else:
            h_r = ""
            for _, r in risers.iterrows():
                tc = get_team_map().get(r['team'], 0)
                # --- PRICE FORMAT FIX (1 decimal) ---
                h_r += f"""<tr><td style="padding-left: 20px;"><div style="display: flex; align-items: center; gap: 10px;">{icon_up}<img src="https://resources.premierleague.com/premierleague/badges/20/t{tc}.png" style="width: 30px;"><div><b>{r['web_name']}</b><br><span style="font-size:0.8rem; color:#AAA;">{r['team']}</span></div></div></td><td style="text-align: center;">£{r['cost']:.1f}</td><td style="text-align: center; color: #00FF85;">+£{r['change']:.1f}</td></tr>"""
            st.markdown(f"""<div class="player-table-container"><table class="modern-table"><thead><tr><th>Player</th><th>Price</th><th>Change</th></tr></thead><tbody>{h_r}</tbody></table></div>""", unsafe_allow_html=True)
            
    with c_f:
        st.subheader("Price Fallers")
        fallers = df_c[df_c['change'] < 0].sort_values('change')
        if fallers.empty: st.info("No fallers.")
        else:
            h_f = ""
            for _, r in fallers.iterrows():
                tc = get_team_map().get(r['team'], 0)
                # --- PRICE FORMAT FIX (1 decimal) ---
                h_f += f"""<tr><td style="padding-left: 20px;"><div style="display: flex; align-items: center; gap: 10px;">{icon_dn}<img src="https://resources.premierleague.com/premierleague/badges/20/t{tc}.png" style="width: 30px;"><div><b>{r['web_name']}</b><br><span style="font-size:0.8rem; color:#AAA;">{r['team']}</span></div></div></td><td style="text-align: center;">£{r['cost']:.1f}</td><td style="text-align: center; color: #FF0055;">{r['change']:.1f}</td></tr>"""
            st.markdown(f"""<div class="player-table-container"><table class="modern-table"><thead><tr><th>Player</th><th>Price</th><th>Change</th></tr></thead><tbody>{h_f}</tbody></table></div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""<div style='text-align: center; color: #B0B0B0;'><p><strong>FPL Metric</strong> | Built for the FPL Community</p><p><a href="https://x.com/FPL_Metric" target="_blank" style="color: #00FF85; text-decoration: none;">Follow on X: @FPL_Metric</a></p></div>""", unsafe_allow_html=True)
