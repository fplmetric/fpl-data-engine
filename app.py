import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="FPL Metric Dashboard", layout="wide")

# Connect to Database using Streamlit Secrets
@st.cache_resource
def get_db_engine():
    # We grab the password from the cloud config, not a local file
    url = st.secrets["DATABASE_URL"]
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url)

try:
    engine = get_db_engine()
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# Sidebar
st.sidebar.header("🔍 Filter Options")
min_minutes = st.sidebar.slider("Min Minutes (Last 48h)", 0, 90, 60)
max_own = st.sidebar.slider("Max Ownership (%)", 0, 100, 15)

# Query
query = f"""
SELECT web_name, team_name, position, cost, selected_by_percent, xg, xa, minutes
FROM human_readable_fpl
WHERE snapshot_time > NOW() - INTERVAL '48 hours'
"""
df = pd.read_sql(query, engine)

# Filter
filtered = df[
    (df['minutes'] >= min_minutes) & 
    (df['selected_by_percent'] <= max_own)
]

# Display
st.title("⚽ FPL Metric Live")
st.metric("Differentials Found", len(filtered))
st.dataframe(
    filtered.sort_values(by='xg', ascending=False),
    use_container_width=True,
    hide_index=True
)
