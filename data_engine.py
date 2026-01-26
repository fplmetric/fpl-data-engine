import streamlit as st
import pandas as pd
import requests
import json
from sqlalchemy import create_engine
from datetime import datetime

# --- DATABASE CONNECTION ---
def get_engine():
    try:
        url = st.secrets["DATABASE_URL"]
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return create_engine(url)
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        return None

engine = get_engine()

# --- API FUNCTIONS ---

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
        processed_fixtures.append({
            'home_name': home_t['name'], 'home_code': home_t['code'],
            'away_name': away_t['name'], 'away_code': away_t['code'],
            'iso_time': f['kickoff_time'] 
        })
    return gw_name, deadline_iso, processed_fixtures

@st.cache_data(ttl=3600)
def get_next_gameweek_id():
    fixtures = requests.get('https://fantasy.premierleague.com/api/fixtures/?future=1').json()
    if fixtures: return fixtures[0]['event']
    return 38 

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

def fetch_main_data():
    query = """
    SELECT DISTINCT ON (player_id)
        player_id, web_name, team_name, position, cost, selected_by_percent, status, news,
        minutes, starts, matches_played, total_points, points_per_game,
        xg, xa, xgi, goals_scored, assists, clean_sheets, goals_conceded, xgc,
        def_cons, tackles, recoveries, cbi, form, value_season, bps
    FROM human_readable_fpl ORDER BY player_id, snapshot_time DESC
    """
    return pd.read_sql(query, engine)

def create_deadline_widget(gw_name, deadline_iso, fixtures_data):
    """
    Generates the HTML string for the deadline widget.
    This prevents indentation errors in the main app file.
    """
    fixtures_json = json.dumps(fixtures_data)
    
    return f"""
    <style>
        .widget-container {{ margin-bottom: 10px; font-family: 'Roboto', sans-serif; }}
        .deadline-box {{
            background: linear-gradient(135deg, #1a001e 0%, #37003c 100%);
            border: 1px solid #00FF85; border-top-left-radius: 12px; border-top-right-radius: 12px;
            padding: 15px; text-align: center; color: white; border-bottom: none;
        }}
        .label {{ color: #00FF85; font-size: 0.9rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px; }}
        .timer {{ font-size: 2.2rem; font-weight: 900; margin: 0; line-height: 1.1; }}
        .sub {{ font-size: 0.85rem; color: #BBB; margin-top: 5px; }}
        
        .fix-container {{
            border: 1px solid #00FF85; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;
            overflow: hidden; background-color: rgba(255, 255, 255, 0.02);
        }}
        .fix-header {{
            background: linear-gradient(90deg, rgba(55,0,60,0.9) 0%, rgba(30,30,30,0.9) 100%);
            padding: 10px 20px; font-weight: 700; color: #00FF85;
            text-align: center; font-family: 'Roboto', sans-serif;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        .content {{ padding: 20px; }}
        .match-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }}
        .match-card {{
            background-color: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; padding: 10px; display: flex; justify-content: space-between; align-items: center;
            transition: transform 0.2s;
        }}
        .match-card:hover {{ border-color: #00FF85; background-color: rgba(255,255,255,0.08); }}
        .team-col {{ display: flex; flex-direction: column; align-items: center; width: 60px; }}
        .team-logo {{ width: 35px; height: 35px; object-fit: contain; margin-bottom: 5px; }}
        .team-name {{ font-size: 0.75rem; font-weight: 700; text-align: center; color: #FFF; }}
        .match-info {{ display: flex; flex-direction: column; align-items: center; color: #AAA; }}
        .match-time {{ font-size: 1rem; font-weight: 700; color: #00FF85; }}
        .match-date {{ font-size: 0.7rem; text-transform: uppercase; }}
    </style>
    
    <div class="widget-container">
        <div class="deadline-box">
            <div class="label">{gw_name} DEADLINE</div>
            <div id="timer" class="timer">Loading...</div>
            <div id="sub" class="sub"></div>
        </div>
        <div class="fix-container">
            <div class="fix-header">{gw_name} Fixtures</div>
            <div class="content">
                <div class="match-grid" id="grid"></div>
            </div>
        </div>
    </div>

    <script>
        var deadline = new Date("{deadline_iso}").getTime();
        var dateOpts = {{ weekday: 'long', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }};
        var subEl = document.getElementById("sub");
        if(subEl) subEl.innerText = new Date("{deadline_iso}").toLocaleDateString(undefined, dateOpts) + " (Local)";
        
        setInterval(function() {{
            var now = new Date().getTime();
            var t = deadline - now;
            var timerEl = document.getElementById("timer");
            if(timerEl) {{
                if (t < 0) {{
                    timerEl.innerHTML = "DEADLINE PASSED";
                    timerEl.style.color = "#FF0055";
                }} else {{
                    var d = Math.floor(t / (1000 * 60 * 60 * 24));
                    var h = Math.floor((t % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    var m = Math.floor((t % (1000 * 60 * 60)) / (1000 * 60));
                    var s = Math.floor((t % (1000 * 60)) / 1000);
                    timerEl.innerHTML = d + "d " + h + "h " + m + "m " + s + "s ";
                }}
            }}
        }}, 1000);

        var fixtures = {fixtures_json};
        var grid = document.getElementById("grid");
        if(grid) {{
            fixtures.forEach(f => {{
                var d = new Date(f.iso_time);
                var timeStr = d.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}});
                var dateStr = d.toLocaleDateString([], {{weekday: 'short', day: 'numeric', month: 'short'}});
                var h_img = "https://resources.premierleague.com/premierleague/badges/50/t" + f.home_code + ".png";
                var a_img = "https://resources.premierleague.com/premierleague/badges/50/t" + f.away_code + ".png";
                
                var card = `
                <div class="match-card">
                    <div class="team-col"><img src="${{h_img}}" class="team-logo"><span class="team-name">${{f.home_name}}</span></div>
                    <div class="match-info"><span class="match-time">${{timeStr}}</span><span class="match-date">${{dateStr}}</span></div>
                    <div class="team-col"><img src="${{a_img}}" class="team-logo"><span class="team-name">${{f.away_name}}</span></div>
                </div>`;
                grid.innerHTML += card;
            }});
        }}
    </script>
    """
