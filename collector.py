import os
import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.types import Integer, Float, String, DateTime, Text

# --- CONFIGURATION ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Supabase connection string fix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def fetch_and_store():
    print(f"[{datetime.now()}] Starting Full Data Dump...")
    
    # 1. Fetch the "Bootstrap" (The Motherlode)
    try:
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"CRITICAL: API Fetch failed - {e}")
        return

    players = data['elements']
    current_timestamp = datetime.now()
    
    # 2. Extract EVERYTHING useful for an App
    # We flatten the data into a list of dictionaries
    all_player_data = []
    
    for p in players:
        row = {
            # --- ID & Context ---
            'snapshot_time': current_timestamp,
            'player_id': p['id'],
            'web_name': p['web_name'],
            'first_name': p['first_name'],
            'second_name': p['second_name'],
            'team_code': p['team'],
            'position_id': p['element_type'],
            
            # --- Status & News (Crucial for App UI) ---
            'status': p['status'], # e.g., 'a' (available), 'd' (doubtful)
            'news': p['news'],     # e.g., "Knee injury - 75% chance"
            'chance_of_playing': p['chance_of_playing_next_round'],
            
            # --- Market Data ---
            'cost': p['now_cost'] / 10.0,
            'selected_by_percent': float(p['selected_by_percent']),
            'transfers_in_event': p['transfers_in_event'],   # Transfers this GW
            'transfers_out_event': p['transfers_out_event'],
            'cost_change_event': p['cost_change_event'],     # Price rise/fall today
            
            # --- The "Points" Stats ---
            'total_points': p['total_points'],
            'points_per_game': float(p['points_per_game']),
            'minutes': p['minutes'],
            'goals_scored': p['goals_scored'],
            'assists': p['assists'],
            'clean_sheets': p['clean_sheets'],
            'goals_conceded': p['goals_conceded'],
            'own_goals': p['own_goals'],
            'penalties_saved': p['penalties_saved'],
            'penalties_missed': p['penalties_missed'],
            'yellow_cards': p['yellow_cards'],
            'red_cards': p['red_cards'],
            'saves': p['saves'],
            'bonus': p['bonus'],
            'bps': p['bps'],
            
            # --- Advanced Underlying Stats (The "Secret Sauce") ---
            'influence': float(p['influence']),
            'creativity': float(p['creativity']),
            'threat': float(p['threat']),
            'ict_index': float(p['ict_index']),
            'xg': float(p['expected_goals']),
            'xa': float(p['expected_assists']),
            'xgi': float(p['expected_goal_involvements']),
            'xgc': float(p['expected_goals_conceded']),
            
            # --- Form Metrics ---
            'form': float(p['form']),
            'value_form': float(p['value_form']),
            'value_season': float(p['value_season'])
        }
        all_player_data.append(row)
    
    # 3. Create DataFrame
    df = pd.DataFrame(all_player_data)
    
    # 4. Upload to Supabase
    # We use explicit SQL types to ensure the database doesn't guess wrong
    dtype_mapping = {
        'snapshot_time': DateTime,
        'news': Text,
        'web_name': String,
        # Most others are auto-detected fine, but these help safety
    }

    try:
        engine = create_engine(DATABASE_URL)
        table_name = 'fpl_full_history'
        
        # 'if_exists="append"' creates the table if it's missing, then adds rows
        df.to_sql(table_name, engine, if_exists='append', index=False, dtype=dtype_mapping)
        
        print(f"SUCCESS: Archived {len(df)} player records to '{table_name}'.")
        
    except Exception as e:
        print(f"Database Upload Failed: {e}")

if __name__ == "__main__":
    fetch_and_store()
