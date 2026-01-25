import requests
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import os
import time

# --- CONFIGURATION ---
DB_URL = os.environ["DATABASE_URL"]

def get_db_connection():
    return psycopg2.connect(DB_URL)

def fetch_fpl_data():
    print("🚀 STARTING COLLECTOR SCRIPT - VERSION: MATCHES_PLAYED_FIX")
    print("🚀 Connecting to FPL API...")
    
    # 1. Get Main Data
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    data = response.json()
    
    elements = data['elements']
    print(f"📦 Fetched {len(elements)} players. Now calculating Matches Played (this takes time)...")
    
    processed_data = []
    
    for i, p in enumerate(elements):
        # --- NEW LOGIC: CALCULATE REAL MATCHES PLAYED ---
        # The main API only gives 'starts'. We must check history to find sub appearances.
        matches_played = 0
        
        # Only fetch history if they have actually played (saves time)
        if p['minutes'] > 0:
            try:
                # We need to hit a different endpoint for every single player
                p_id = p['id']
                history_url = f"https://fantasy.premierleague.com/api/element-summary/{p_id}/"
                h_resp = requests.get(history_url)
                
                if h_resp.status_code == 200:
                    history_data = h_resp.json()
                    # Count every game where they played at least 1 minute
                    matches_played = sum(1 for game in history_data['history'] if game['minutes'] > 0)
                else:
                    # Fallback if request fails
                    matches_played = p['starts']
            except Exception as e:
                print(f"⚠️ Could not fetch history for {p['web_name']}: {e}")
                matches_played = p['starts']
        else:
            matches_played = 0

        # Log progress every 50 players so you know it's working
        if i % 50 == 0:
            print(f"   ...Processed {i}/{len(elements)} players")
        # -------------------------------------------------------

        # We use 'player_id' instead of 'id'
        player_row = {
            "player_id": p['id'],  
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
            "matches_played": matches_played, # <--- UPDATED THIS LINE

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
        
    return processed_data

def save_to_supabase(data):
    if not data: return
    conn = get_db_connection()
    cursor = conn.cursor()
    columns = data[0].keys()
    
    # SAFETY CHECK
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
