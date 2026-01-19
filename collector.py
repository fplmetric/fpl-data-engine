import requests
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import os

# --- CONFIGURATION ---
DB_URL = os.environ["DATABASE_URL"]

def get_db_connection():
    return psycopg2.connect(DB_URL)

def fetch_fpl_data():
    print("🚀 Connecting to FPL API...")
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    data = response.json()
    
    elements = data['elements']
    processed_data = []
    
    for p in elements:
        player_row = {
            "id": p['id'],
            "web_name": p['web_name'],
            "team_code": p['team'],
            "position_id": p['element_type'],
            "status": p['status'],
            "news": p['news'],
            
            # Economics
            "cost": p['now_cost'] / 10.0,
            "selected_by_percent": float(p['selected_by_percent']),
            "value_form": float(p.get('value_form', 0)),
            "value_season": float(p.get('value_season', 0)),
            "form": float(p.get('form', 0)),

            # Activity
            "minutes": p['minutes'],
            "total_points": p['total_points'],
            "points_per_game": float(p['points_per_game']),
            "starts": p.get('starts', 0), 
            "matches_played": p.get('starts', 0), 

            # Attack
            "goals_scored": p['goals_scored'],
            "assists": p['assists'],
            
            # Defense (The 2026 Suite)
            "clean_sheets": p['clean_sheets'],
            "goals_conceded": p['goals_conceded'],
            "own_goals": p.get('own_goals', 0),
            "penalties_saved": p.get('penalties_saved', 0),
            "defensive_contributions": p.get('defensive_contributions', 0),
            "tackles": p.get('tackles', 0),
            "recoveries": p.get('recoveries', 0),
            "cbi": p.get('clearances_blocks_interceptions', 0),

            # Underlying Data (xStats)
            "xg": float(p.get('expected_goals', 0)),
            "xa": float(p.get('expected_assists', 0)),
            "xgi": float(p.get('expected_goal_involvements', 0)),
            "xgc": float(p.get('expected_goals_conceded', 0)),

            # BPS & ICT
            "bonus": p.get('bonus', 0),
            "bps": p.get('bps', 0),
            "influence": float(p.get('influence', 0)),
            "creativity": float(p.get('creativity', 0)),
            "threat": float(p.get('threat', 0)),
            "ict_index": float(p.get('ict_index', 0)),

            "snapshot_time": datetime.now().isoformat()
        }
        processed_data.append(player_row)

    return processed_data

def save_to_supabase(data):
    if not data: return
    conn = get_db_connection()
    cursor = conn.cursor()
    columns = data[0].keys()
    query = "INSERT INTO fpl_full_history ({}) VALUES %s".format(','.join(columns))
    values = [[row[col] for col in columns] for row in data]
    try:
        execute_values(cursor, query, values)
        conn.commit()
        print("✅ Data successfully saved!")
    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    player_data = fetch_fpl_data()
    save_to_supabase(player_data)
