import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Page Config (Tab Title & Layout)
st.set_page_config(page_title="FPL Metric Dashboard", layout="wide")

# 2. Database Connection (Cached so it doesn't reload on every click)
@st.cache_resource
def get_db_engine():
    # Fetch secret from .streamlit/secrets.toml
    url = st.secrets["connections"]["DATABASE_URL"]
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url)

try:
    engine = get_db_engine()
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

# 3. Sidebar Filters
st.sidebar.header("🔍 Filter Options")
selected_pos = st.sidebar.multiselect("Position", ['GKP', 'DEF', 'MID', 'FWD'], default=['DEF', 'MID', 'FWD'])
max_price = st.sidebar.slider("Max Price (£m)", 4.0, 14.0, 14.0, 0.1)
max_own = st.sidebar.slider("Max Ownership (%)", 0.1, 100.0, 15.0, 0.5)
min_minutes = st.sidebar.number_input("Min Minutes Played", 0, 9000, 60)

# 4. Fetch Data (Only from your Clean View)
query = """
SELECT web_name, team_name, position, cost, selected_by_percent, xg, xa, minutes, status
FROM human_readable_fpl
WHERE snapshot_time > NOW() - INTERVAL '48 hours'
"""
# Load into DataFrame
df = pd.read_sql(query, engine)

# 5. Apply User Filters
filtered_df = df[
    (df['position'].isin(selected_pos)) &
    (df['cost'] <= max_price) &
    (df['selected_by_percent'] <= max_own) &
    (df['minutes'] >= min_minutes)
]

# 6. Main Dashboard Layout
st.title("⚽ FPL Metric: The Hidden Floor")
st.markdown(f"Found **{len(filtered_df)}** players matching your criteria.")

# Highlight Metrics
col1, col2, col3 = st.columns(3)
if not filtered_df.empty:
    best_xg = filtered_df.loc[filtered_df['xg'].idxmax()]
    col1.metric("Top xG Threat", f"{best_xg['web_name']} ({best_xg['team_name']})", f"{best_xg['xg']} xG")
    
    cheapest_starter = filtered_df.sort_values('cost').iloc[0]
    col2.metric("Cheapest Enabler", f"{cheapest_starter['web_name']}", f"£{cheapest_starter['cost']}m")

# The Data Table
st.dataframe(
    filtered_df.sort_values(by='xg', ascending=False),
    column_config={
        "web_name": "Player",
        "team_name": "Team",
        "xg": st.column_config.NumberColumn("Exp. Goals (xG)", format="%.2f"),
        "xa": st.column_config.NumberColumn("Exp. Assists (xA)", format="%.2f"),
        "selected_by_percent": st.column_config.ProgressColumn("Ownership %", format="%.1f%%", min_value=0, max_value=100),
    },
    hide_index=True,
    use_container_width=True
)
