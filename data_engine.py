import streamlit as st
import pandas as pd
import requests
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
        
        # We now return the raw 'kickoff_time' (ISO format) for JS to handle
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

# --- FETCH MAIN DATA ---
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
