import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components
import requests
from collections import defaultdict
import os

# --- LOCAL IMPORTS ---
import styles
import data_engine as db

# --- 1. SETUP ---
st.set_page_config(page_title="FPL Metric Dashboard", page_icon="favicon.png", layout="wide")

# --- GLOBAL CSS ---
st.markdown(styles.GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Roboto:wght@400;700&display=swap');
    
    h1, h2, h3, .stMetricLabel, [data-baseweb="tab"], .big-font { font-family: 'Orbitron', sans-serif !important; letter-spacing: 1px; }
    ::-webkit-scrollbar { width: 8px; height: 8px; background: #1a001e; }
    ::-webkit-scrollbar-thumb { background: #00FF85; border-radius: 4px; }
    ::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); }
    section[data-testid="stSidebar"] { background-color: rgba(20, 0, 30, 0.95); border-right: 1px solid rgba(0, 255, 133, 0.2); }
    section[data-testid="stSidebar"] > div { background-color: transparent; }
    div[data-baseweb="slider"] div[role="slider"] { background-color: #00FF85 !important; }
    div[data-baseweb="slider"] div[data-testid="stTickBar"] { background: linear-gradient(to right, #00FF85, #00FF85) !important; }
    span[data-baseweb="checkbox"] div[class*="checked"] { background-color: #00FF85 !important; border-color: #00FF85 !important; }
    div[data-baseweb="input"] { background-color: rgba(255, 255, 255, 0.05) !important; border-color: rgba(0, 255, 133, 0.3) !important; color: white !important; border-radius: 8px !important; }
    div[data-testid="InputInstructions"] { display: none !important; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 8px; border: 1px solid rgba(0, 255, 133, 0.2); gap: 8px; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { height: auto; background-color: transparent; border: 1px solid transparent; color: #AAAAAA; font-weight: 700; border-radius: 8px; padding: 12px 24px; transition: all 0.3s ease; }
    .stTabs [data-baseweb="tab"]:hover { background-color: rgba(255, 255, 255, 0.08); color: #FFFFFF; }
    .stTabs [aria-selected="true"] { background-color: rgba(0, 255, 133, 0.15) !important; color: #00FF85 !important; border: 1px solid #00FF85 !important; box-shadow: 0 0 15px rgba(0, 255, 133, 0.2); }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    /* Table */
    .player-table-container, .fixture-table-container { margin-top: 0px; overflow-x: auto !important; -webkit-overflow-scrolling: touch; padding-bottom: 10px; }
    .modern-table { width: 100%; border-collapse: separate; border-spacing: 0 8px; font-family: 'Roboto', sans-serif; color: #E0E0E0; min-width: 800px; }
    .modern-table th { background-color: #1a001e !important; color: #00FF85; font-family: 'Orbitron', sans-serif; font-weight: 700; padding: 15px; text-align: center; border-bottom: none !important; position: sticky; top: 0; z-index: 1000; box-shadow: 0 2px 0 #00FF85; }
    .modern-table th::before { content: ""; position: absolute; top: -20px; left: 0; right: 0; height: 20px; background-color: #1a001e; z-index: -1; }
    .modern-table tbody tr { transition: all 0.2s ease; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 1; }
    .modern-table tbody tr:hover { transform: scale(1.005); box-shadow: 0 5px 15px rgba(0, 255, 133, 0.15); position: relative; z-index: 10; }
    .modern-table td { padding: 12px; vertical-align: middle; border-top: 1px solid rgba(255, 255, 255, 0.05); border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
    .modern-table td:first-child { border-top-left-radius: 8px; border-bottom-left-radius: 8px; }
    .modern-table td:last-child { border-top-right-radius: 8px; border-bottom-right-radius: 8px; border-right: 1px solid rgba(255, 255, 255, 0.05); }
    
    /* Fixture Pills Layout - FIXED */
    .mini-fix-container { 
        display: flex; 
        gap: 6px; 
        justify-content: center; 
        align-items: flex-start;
    }
    
    /* Individual Slot for a Gameweek */
    .fix-slot {
        display: flex;
        flex-direction: column;
        gap: 2px;
        width: 38px; /* Fixed width per GW to ensure alignment */
    }

    .mini-fix-box { 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        width: 38px; 
        height: 24px; 
        border-radius: 4px; 
        font-size: 0.75rem; 
        font-weight: 900; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.3); 
    }
    
    .diff-badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; display: block; width: 100%; text-align: center; margin-bottom: 2px;}
    div[data-testid="stSidebar"] button { border-radius: 10px !important; height: 3em !important; font-family: 'Orbitron', sans-serif !important; font-weight: 700 !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    
    @media only screen and (max-width: 768px) {
        h1 { font-size: 1.8rem !important; }
        .block-container { padding-top: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
        .player-table-container { overflow-x: scroll !important; }
        .modern-table th, .modern-table td { padding: 8px !important; font-size: 0.8rem !important; }
        img[alt="fpl_metric_logo.png"] { width: 80% !important; margin: 0 auto; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. ROBUST DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_bootstrap():
    try:
        r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", headers={'User-Agent': 'Mozilla/5.0'})
        return r.json() if r.status_code == 200 else {}
    except: return {}

@st.cache_data(ttl=3600)
def fetch_all_fixtures():
    try:
        r = requests.get("https://fantasy.premierleague.com/api/fixtures/", headers={'User-Agent': 'Mozilla/5.0'})
        return r.json() if r.status_code == 200 else []
    except: return []

# Get Core Data
bootstrap = fetch_bootstrap()
raw_fixtures = fetch_all_fixtures()

# --- CRITICAL: NAME NORMALIZATION & MAPPING ---
teams = bootstrap.get('teams', [])

# 1. Base Maps from API Data
id_to_name = {t['id']: t['name'] for t in teams}
id_to_short = {t['id']: t['short_name'] for t in teams}
id_to_code = {t['id']: t['code'] for t in teams}

# 2. Robust Name-to-ID Map (Handles "Nottingham Forest" vs "Nott'm Forest")
name_to_id = {}
for t in teams:
    # Add API Name (e.g. "Nott'm Forest")
    name_to_id[t['name']] = t['id']
    # Add Short Name (e.g. "NFO")
    name_to_id[t['short_name']] = t['id']
    
    # Add Custom Overrides for known mismatches
    if t['short_name'] == "NFO": 
        name_to_id["Nottingham Forest"] = t['id']
        name_to_id["Nottm Forest"] = t['id']
    if t['short_name'] == "SHU": name_to_id["Sheffield United"] = t['id']
    if t['short_name'] == "LUT": name_to_id["Luton Town"] = t['id']
    if t['short_name'] == "MUN": name_to_id["Manchester United"] = t['id']
    if t['short_name'] == "MCI": name_to_id["Manchester City"] = t['id']
    if t['short_name'] == "NEW": name_to_id["Newcastle United"] = t['id']
    if t['short_name'] == "TOT": name_to_id["Tottenham Hotspur"] = t['id']
    if t['short_name'] == "WOL": name_to_id["Wolverhampton Wanderers"] = t['id']

# Global FDR Colors
fdr = {1:'#375523', 2:'#00FF85', 3:'#EBEBEB', 4:'#FF0055', 5:'#680808'}

# Determine Current GW
events = bootstrap.get('events', [])
current_gw_obj = next((e for e in events if e['is_next']), events[0] if events else None)
current_gw_id = current_gw_obj['id'] if current_gw_obj else 1
gw_name_str = current_gw_obj['name'] if current_gw_obj else "Gameweek 1"
deadline_str = current_gw_obj['deadline_time'] if current_gw_obj else ""

# Process Upcoming Fixtures
team_upcoming = defaultdict(list)
gw_fixtures_display = [] 

for f in raw_fixtures:
    if f['event'] is None: continue
    
    # Widget Data
    if f['event'] == current_gw_id:
        h_code = id_to_code.get(f['team_h'])
        a_code = id_to_code.get(f['team_a'])
        gw_fixtures_display.append({
            'home_name': id_to_short.get(f['team_h']), 'away_name': id_to_short.get(f['team_a']),
            'home_code': h_code, 'away_code': a_code,
            'iso_time': f['kickoff_time']
        })

    # Future Fixtures Data (Mapped by Team ID to be safe)
    if f['event'] >= current_gw_id:
        h_id = f['team_h']
        a_id = f['team_a']
        
        team_upcoming[h_id].append({
            'event': f['event'],
            'opp': id_to_short.get(a_id) + " (H)",
            'diff': f['team_h_difficulty'],
            'kickoff': f['kickoff_time']
        })
        team_upcoming[a_id].append({
            'event': f['event'],
            'opp': id_to_short.get(h_id) + " (A)",
            'diff': f['team_a_difficulty'],
            'kickoff': f['kickoff_time']
        })

for t in team_upcoming:
    team_upcoming[t].sort(key=lambda x: x['kickoff'])

# Get next 5 distinct GW IDs
all_future_gws = sorted(list(set(f['event'] for t in team_upcoming for f in team_upcoming[t] if f['event'] >= current_gw_id)))
next_5_gw_ids = all_future_gws[:5]

# --- LOAD PLAYER DATA ---
df = db.fetch_main_data()
df = df.fillna(0)

df['matches_played'] = df['matches_played'].replace(0, 1)
df['minutes'] = df['minutes'].replace(0, 1)
df['avg_minutes'] = df['minutes'] / df['matches_played']
df['xgi_per_90'] = (df['xgi'] / df['minutes']) * 90
df['xgc_per_90'] = (df['xgc'] / df['minutes']) * 90
df['dc_per_90'] = (df['def_cons'] / df['minutes']) * 90
df['tackles_per_90'] = (df['tackles'] / df['minutes']) * 90
ep_map = db.get_expected_points_map()
df['ep_next'] = df['player_id'].map(ep_map).fillna(0.0)

# --- HISTORY FETCHING ---
@st.cache_data(ttl=3600)
def get_real_player_history(player_id, _team_map):
    try:
        r = requests.get(f"https://fantasy.premierleague.com/api/element-summary/{int(player_id)}/", headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200: return []
        data = r.json()
        history = data.get('history', [])[-5:]
        formatted = []
        for m in history:
            opp_info = _team_map.get(m['opponent_team'], {'code': 0, 'short_name': 'UNK'})
            pts = m['total_points']
            color = "#00FF85" if pts >= 7 else "#EBEBEB" if pts <= 2 else "#FFCC00"
            formatted.append({
                "gw": f"GW{m['round']}", "opp_code": opp_info['code'], "opp_name": opp_info['short_name'],
                "pts": pts, "color": color, "text_color": "#000" if pts >= 3 else "#333"
            })
        return formatted
    except: return []

def render_player_profile(player_row):
    hist = get_real_player_history(player_row['player_id'], {t['id']: {'code': t['code'], 'short_name': t['short_name']} for t in teams})
    
    # Robust Badge Look up
    t_id = name_to_id.get(player_row['team_name'])
    t_code = id_to_code.get(t_id, 0)
    
    h_html = ""
    if hist:
        for h in hist:
            h_html += f"""<div style="flex: 1; display: flex; flex-direction: column; align-items: center; background: rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; min-width: 70px;"><span style="color: #AAA; font-size: 0.7rem; margin-bottom: 5px;">{h['gw']}</span><img src="https://resources.premierleague.com/premierleague/badges/50/t{h['opp_code']}.png" style="width: 30px; margin-bottom: 5px;"><span style="color: #FFF; font-weight: bold; font-size: 0.8rem; margin-bottom: 5px;">{h['opp_name']}</span><div style="background-color: {h['color']}; color: {h['text_color']}; border-radius: 12px; padding: 2px 10px; font-weight: 900; font-size: 0.9rem;">{h['pts']}pts</div></div>"""
    else: h_html = "<div style='color: #AAA;'>No history.</div>"
    
    st.markdown(f"""<div style="background: linear-gradient(180deg, rgba(20,0,30,1) 0%, rgba(40,0,50,1) 100%); border: 1px solid #00FF85; border-radius: 15px; padding: 20px; margin-bottom: 20px; box-shadow: 0 0 20px rgba(0, 255, 133, 0.2);"><div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 20px;"><div style="display: flex; align-items: center; gap: 20px;"><div style="width: 80px; height: 80px; border-radius: 50%; overflow: hidden; border: 2px solid #00FF85; background: #FFF;"><img src="https://resources.premierleague.com/premierleague/badges/50/t{t_code}.png" style="width: 100%; height: 100%; object-fit: cover; padding: 10px;"></div><div><h2 style="margin: 0; color: #FFF; font-size: 1.8rem;">{player_row['web_name']}</h2><p style="margin: 0; color: #00FF85; font-size: 1rem; font-weight: bold;">{player_row['team_name']} | {player_row['position']}</p></div></div><div style="text-align: right;"><div style="font-size: 0.9rem; color: #AAA;">Current Price</div><div style="font-size: 2rem; font-weight: 900; color: #FFF;">£{player_row['cost']}</div></div></div><div style="margin-top: 25px;"><h4 style="color: #FFF; font-family: 'Orbitron', sans-serif; margin-bottom: 15px;">Form (Last 5 Matches)</h4><div style="display: flex; gap: 10px; justify-content: space-between; overflow-x: auto;">{h_html}</div></div></div>""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    if "fpl_metric_logo.png" in [f.name for f in os.scandir(".")]: st.image("fpl_metric_logo.png", use_container_width=True)
    st.header("Filters")
    all_teams = sorted(df['team_name'].unique())
    if 'team_selection' not in st.session_state: st.session_state['team_selection'] = all_teams
    def select_all(): st.session_state['team_selection'] = all_teams
    def clear_all(): st.session_state['team_selection'] = []
    c1, c2 = st.columns(2)
    with c1: st.button("✅ All", on_click=select_all, use_container_width=True)
    with c2: st.button("❌ Clear", on_click=clear_all, use_container_width=True)
    with st.form("f"):
        s_teams = st.multiselect("Teams", all_teams, default=all_teams, key='team_selection')
        pos = st.multiselect("Position", ["GKP", "DEF", "MID", "FWD"], default=["DEF", "MID", "FWD"])
        ex_un = st.checkbox("Exclude Red Flags")
        mx_p = st.slider("Max Price", 3.5, 15.0, 15.0, 0.1)
        mx_o = st.slider("Max Own%", 0, 100, 100)
        st.subheader("Stats")
        mn_mpg = st.slider("Min Mins", 0, 90, 0)
        mn_ppg = st.slider("Min PPG", 0.0, 10.0, 0.0)
        mn_dc = st.slider("Min DC/90", 0.0, 10.0, 0.0)
        st.form_submit_button("Apply")

df = df[df['minutes'] >= 90]
if ex_un: df = df[~df['status'].isin(['i','u','n','s'])]
filtered = df[(df['team_name'].isin(s_teams)) & (df['position'].isin(pos)) & (df['cost']<=mx_p) & (df['selected_by_percent']<=mx_o) & (df['avg_minutes']>=mn_mpg) & (df['points_per_game']>=mn_ppg) & (df['dc_per_90']>=mn_dc)]

# --- MAIN UI ---
if "fpl_metric_logo.png" in [f.name for f in os.scandir(".")]: 
    _, cm, _ = st.columns([3, 2, 3])
    with cm: st.image("fpl_metric_logo.png", use_container_width=True)

# FIXTURE WIDGET
if gw_fixtures_display:
    fix_json = json.dumps(gw_fixtures_display)
    comp_html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@400;700&display=swap');
        .w {{ font-family: 'Roboto', sans-serif; }}
        .d {{ background: linear-gradient(135deg, #1a001e 0%, #37003c 100%); border: 1px solid #00FF85; border-radius: 12px 12px 0 0; padding: 15px; text-align: center; color: white; }}
        .lbl {{ color: #00FF85; font-weight: 700; letter-spacing: 2px; }}
        .tm {{ font-size: 2rem; font-weight: 900; font-family: 'Orbitron'; margin: 0; }}
        .cnt {{ background: rgba(255,255,255,0.02); border: 1px solid #00FF85; border-top: none; border-radius: 0 0 12px 12px; padding: 15px; }}
        .grd {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }}
        .c {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; display: flex; justify-content: space-between; align-items: center; width: 280px; min-width: 280px; }}
        .tc {{ display: flex; flex-direction: column; align-items: center; width: 60px; }}
        .tn {{ font-size: 0.75rem; font-weight: 700; color: #FFF; }}
        .mi {{ display: flex; flex-direction: column; align-items: center; color: #AAA; font-size: 0.8rem; }}
        .mt {{ color: #00FF85; font-weight: 700; font-family: 'Orbitron'; }}
        @media(max-width:768px){{ 
            .cnt {{ max-height: 500px; overflow-y: auto; -webkit-overflow-scrolling: touch; padding-bottom: 15px; }}
            .grd {{ flex-direction: column; align-items: stretch; flex-wrap: nowrap; gap: 10px; }}
            .c {{ width: 100%; min-width: 0; max-width: none; }}
        }}
    </style>
    <div class="w">
        <div class="d"><div class="lbl">{gw_name_str} DEADLINE</div><div id="t" class="tm">--:--:--</div></div>
        <div class="cnt"><div class="grd" id="g"></div></div>
    </div>
    <script>
        var d = new Date("{deadline_str}").getTime();
        setInterval(function() {{
            var n = new Date().getTime();
            var t = d - n;
            var el = document.getElementById("t");
            if(t<0) {{ el.innerHTML = "DEADLINE PASSED"; el.style.color="#FF0055"; }}
            else {{
                var days = Math.floor(t/(1000*60*60*24));
                var hrs = Math.floor((t%(1000*60*60*24))/(1000*60*60));
                var mins = Math.floor((t%(1000*60*60))/(1000*60));
                el.innerHTML = days + "d " + hrs + "h " + mins + "m";
            }}
        }}, 1000);
        var fx = {fix_json};
        var g = document.getElementById("g");
        fx.forEach(f => {{
            var dt = new Date(f.iso_time);
            var ts = dt.toLocaleTimeString([], {{hour:'2-digit', minute:'2-digit'}});
            var ds = dt.toLocaleDateString([], {{weekday:'short', day:'numeric'}});
            g.innerHTML += `<div class="c"><div class="tc"><img src="https://resources.premierleague.com/premierleague/badges/50/t${{f.home_code}}.png" width="30"><span class="tn">${{f.home_name}}</span></div><div class="mi"><span class="mt">${{ts}}</span><span>${{ds}}</span></div><div class="tc"><img src="https://resources.premierleague.com/premierleague/badges/50/t${{f.away_code}}.png" width="30"><span class="tn">${{f.away_name}}</span></div></div>`;
        }});
    </script>
    """
    components.html(comp_html, height=400, scrolling=False)

st.markdown("""<h1 style='text-align: center; background: linear-gradient(to right, #00FF85, #FFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>FPL Metric Dashboard</h1>""", unsafe_allow_html=True)

# METRICS
c1,c2,c3,c4 = st.columns(4)
if not filtered.empty:
    def crd(t, n, v): return f"""<div style="background:rgba(255,255,255,0.03); border:1px solid #00FF85; border-radius:10px; padding:15px; text-align:center;"><div style="color:#AAA; font-size:0.8rem; font-weight:700;">{t}</div><div style="font-size:1.2rem; font-weight:900;">{n}</div><div style="color:#00FF85; font-weight:bold;">{v}</div></div>"""
    with c1: st.markdown(crd("Threat King", filtered.sort_values('xgi', ascending=False).iloc[0]['web_name'], filtered.sort_values('xgi', ascending=False).iloc[0]['xgi']), unsafe_allow_html=True)
    with c2: st.markdown(crd("Work Rate", filtered.sort_values('dc_per_90', ascending=False).iloc[0]['web_name'], round(filtered.sort_values('dc_per_90', ascending=False).iloc[0]['dc_per_90'],2)), unsafe_allow_html=True)
    with c3: st.markdown(crd("Best Value", filtered.sort_values('value_season', ascending=False).iloc[0]['web_name'], filtered.sort_values('value_season', ascending=False).iloc[0]['value_season']), unsafe_allow_html=True)
    with c4: st.markdown(crd("Best PPG", filtered.sort_values('points_per_game', ascending=False).iloc[0]['web_name'], filtered.sort_values('points_per_game', ascending=False).iloc[0]['points_per_game']), unsafe_allow_html=True)

def render_table(df, cols, key):
    c1, c2, c3 = st.columns([1, 1.5, 1.5])
    with c1: 
        s_lbl = st.selectbox("Sort by:", ["Price", "Ownership", "Matches", "Fixtures"] + list(cols.values()), key=key)
        s_col = {v:k for k,v in cols.items()}.get(s_lbl, s_lbl.lower().replace("price","cost").replace("ownership","selected_by_percent").replace("matches","matches_played").replace("fixtures","fixture_ease"))
    with c2: search = st.text_input("Find Player", key=f"s_{key}")
    
    if search: df = df[df['web_name'].str.contains(search, case=False)]
    
    if s_col == 'fixture_ease':
        ease_map = {}
        for t_name in df['team_name'].unique():
            t_id = name_to_id.get(t_name)
            if t_id:
                fixs = team_upcoming.get(t_id, [])
                total_diff = sum(f['diff'] for f in fixs[:5])
                ease_map[t_name] = 30 - total_diff 
        df['fixture_ease'] = df['team_name'].map(ease_map).fillna(0)

    sorted_df = df.sort_values(s_col, ascending=False).head(100)
    
    with c3:
        p_opts = ["Select..."] + sorted_df['web_name'].tolist()
        sel_p = st.selectbox("Details", p_opts, index=1 if len(sorted_df)==1 else 0, key=f"v_{key}")
    
    if sel_p != "Select...":
        render_player_profile(sorted_df[sorted_df['web_name']==sel_p].iloc[0])

    heads = "".join([f"<th>{h}</th>" for h in ["Player", "Next 5"] + ["Price", "Own%", "Matches"] + list(cols.values())])
    rows = ""
    
    for _, r in sorted_df.iterrows():
        t_id = name_to_id.get(r['team_name'])
        t_code = id_to_code.get(t_id, 0)
        
        # FIX: FIXTURE PILLS LAYOUT (5 SLOTS ONLY)
        fix_html = '<div class="mini-fix-container">'
        
        # Iterate over the next 5 specific Gameweek IDs
        for gw_id in next_5_gw_ids:
            # Get matches for THIS specific gameweek for this team
            matches = [f for f in team_upcoming.get(t_id, []) if f['event'] == gw_id]
            
            # Start Slot
            fix_html += '<div class="fix-slot">'
            
            if not matches:
                # Blank Gameweek (Gray Dash)
                fix_html += '<div class="mini-fix-box" style="background:#222; color:#555;">-</div>'
            else:
                # Loop through matches (1 if single, 2 if double)
                for m in matches:
                    bg = fdr.get(m['diff'], '#333')
                    txt = 'white' if m['diff'] in [1,4,5] else 'black'
                    fix_html += f'<div class="mini-fix-box" style="background:{bg}; color:{txt};" title="GW{m["event"]}">{m["opp"]}</div>'
            
            # End Slot
            fix_html += '</div>'
            
        fix_html += '</div>'
        
        stats_html = ""
        for k in ['cost', 'selected_by_percent', 'matches_played'] + list(cols.keys()):
            val = r[k]
            if k == 'cost': val = f"£{val}"
            elif k == 'selected_by_percent': val = f"{val}%"
            elif isinstance(val, float): val = f"{val:.1f}"
            stats_html += f"<td style='text-align:center;'>{val}</td>"
            
        rows += f"""<tr style="background:rgba(255,255,255,0.03);">
        <td style="padding-left:10px;"><div style="display:flex;align-items:center;gap:10px;"><img src="https://resources.premierleague.com/premierleague/badges/20/t{t_code}.png" width="30"><div><b>{r['web_name']}</b><br><span style="font-size:0.8rem;color:#AAA;">{r['team_name']}</span></div></div></td>
        <td style="text-align:center;">{fix_html}</td>
        {stats_html}</tr>"""
        
    st.markdown(f"""<div class="player-table-container"><table class="modern-table"><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["Overview", "Attack", "Defense", "Work Rate"])
with t1: render_table(filtered, {"ep_next":"XP", "total_points":"Pts", "points_per_game":"PPG"}, "t1")
with t2: render_table(filtered, {"xgi":"xGI", "goals_scored":"Goals", "assists":"Assists"}, "t2")
with t3: render_table(filtered, {"clean_sheets":"CS", "xgc":"xGC", "goals_conceded":"GC"}, "t3")
with t4: render_table(filtered, {"dc_per_90":"DC/90", "tackles":"Tackles", "cbi":"CBI"}, "t4")

# --- TICKER ---
st.markdown("---")
st.header("Fixture Difficulty Ticker")
ticker_data = []

# Use ID map to iterate correctly
for t_name in all_teams:
    t_id = name_to_id.get(t_name)
    if not t_id: continue # Skip if no ID found (shouldn't happen with robust map)
    
    t_code = id_to_code.get(t_id, 0)
    row = {'Team': t_name, 'Logo': f"https://resources.premierleague.com/premierleague/badges/20/t{t_code}.png"}
    
    fixtures = team_upcoming.get(t_id, [])
    row['Diff_Sum'] = sum(f['diff'] for f in fixtures if f['event'] in next_5_gw_ids)
    
    for gw in next_5_gw_ids:
        matches = [f for f in fixtures if f['event'] == gw]
        cell_html = ""
        if not matches: cell_html = "-"
        else:
            for m in matches:
                bg = fdr.get(m['diff'], '#333')
                txt = 'white' if m['diff'] in [1,4,5] else 'black'
                cell_html += f'<span class="diff-badge" style="background:{bg}; color:{txt}; margin-bottom:2px;">{m["opp"]}</span>'
        row[f"GW{gw}"] = cell_html
    ticker_data.append(row)

ticker_df = pd.DataFrame(ticker_data).sort_values('Diff_Sum')
tick_heads = "".join([f"<th>GW{gw}</th>" for gw in next_5_gw_ids])
tick_rows = ""
for _, r in ticker_df.iterrows():
    cells = "".join([f"<td>{r[f'GW{gw}']}</td>" for gw in next_5_gw_ids])
    tick_rows += f"<tr><td style='padding-left:10px; display:flex; align-items:center;'><img src='{r['Logo']}' width='25' style='margin-right:10px;'><b>{r['Team']}</b></td>{cells}</tr>"

st.markdown(f"""<div class="fixture-table-container"><table class="modern-table"><thead><tr><th>Team</th>{tick_heads}</tr></thead><tbody>{tick_rows}</tbody></table></div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align:center; color:#AAA;'>FPL Metric</div>", unsafe_allow_html=True)
