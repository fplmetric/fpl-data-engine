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
    print("🚀 STARTING COLLECTOR SCRIPT - VERSION: FIX_ID_COLLISION_V2") # <--- LOOK FOR THIS IN LOGS
    print("🚀 Connecting to FPL API...")
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    data = response.json()
    
    elements = data['elements']
    print(f"📦 Fetched {len(elements)} players.")
    
    processed_data = []
    
    for p in elements:
        # --- CRITICAL FIX ---
        # We use 'player_id' instead of 'id'
        # We DO NOT send an 'id' key to the database
        player_row = {
            "player_id": p['id'],  # Stores FPL ID (e.g., 3) in a safe column
            "web_name": p['web_name'],
            "team_code": p['team'],
            "position_id": p['element_type'],
            "status": p['status'],
            "news": p['news'],
            
            # --- ECONOMICS ---
            "cost": p['now_cost'] / 10.0,
            "selected_by_percent": float(p['selected_by_percent']),
            "transfers_in_event": p.get('transfers_in_event', 0),
            "transfers_out_event": p.get('transfers_out_event', 0),
            "value_form": float(p.get('value_form', 0)),
            "value_season": float(p.get('value_season', 0)),
            "form": float(p.get('form', 0)),

            # --- ACTIVITY ---
            "minutes": p['minutes'],
            "total_points": p['total_points'],
            "points_per_game": float(p['points_per_game']),
            "starts": p.get('starts', 0), 
            "matches_played": p.get('starts', 0), 

            # --- ATTACK ---
            "goals_scored": p['goals_scored'],
            "assists": p['assists'],
            
            # --- DEFENSE ---
            "clean_sheets": p.get('clean_sheets', 0),
            "goals_conceded": p.get('goals_conceded', 0),
            "own_goals": p.get('own_goals', 0),
            "penalties_saved": p.get('penalties_saved', 0),
            "defensive_contributions": p.get('defensive_contribution', 0),
            "tackles": p.get('tackles', 0),
            "recoveries": p.get('recoveries', 0),
            "cbi": p.get('clearances_blocks_interceptions', 0),

            # --- UNDERLYING ---
            "xg": float(p.get('expected_goals', 0)),
            "xa": float(p.get('expected_assists', 0)),
            "xgi": float(p.get('expected_goal_involvements', 0)),
            "xgc": float(p.get('expected_goals_conceded', 0)),

            # --- BPS ---
            "bonus": p.get('bonus', 0),
            "bps": p.get('bps', 0),
            "ict_index": float(p.get('ict_index', 0)),

            "snapshot_time": datetime.now().isoformat()
        }
        processed_data.append(player_row)
        
        # DEBUG CHECK
        if p['web_name'] == 'Collins':
            print(f"🕵️ VERIFY COLLINS: DC={player_row['defensive_contributions']}, Tackles={player_row['tackles']}")

    return processed_data

def save_to_supabase(data):
    if not data: return
    conn = get_db_connection()
    cursor = conn.cursor()
    columns = data[0].keys()
    
    # SAFETY CHECK: If 'id' is in columns, STOP immediately
    if 'id' in columns:
        print("❌ CRITICAL ERROR: The 'id' key is still present! Script is not updated.")
        return

    query = "INSERT INTO fpl_full_history ({}) VALUES %s".format(','.join(columns))
    values = [[row[col] for col in columns] for row in data]
    try:
        execute_values(cursor, query, values)
        conn.commit()
        print(f"✅ Successfully saved {len(data)} rows to Supabase!")
    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    player_data = fetch_fpl_data()
    save_to_supabase(player_data)
