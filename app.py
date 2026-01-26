import streamlit as st
import pandas as pd
import os
import json
import streamlit.components.v1 as components

# --- LOCAL IMPORTS ---
import styles
import data_engine as db

# --- 1. SETUP ---
st.set_page_config(page_title="FPL Metric Dashboard", page_icon="favicon.png", layout="wide")

# --- GLOBAL CSS: VISUAL ENHANCEMENTS ---
st.markdown(styles.GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
    /* 1. IMPORT FUTURISTIC FONT */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Roboto:wght@400;700&display=swap');

    /* Apply Font to Headings and Tabs */
    h1, h2, h3, .stMetricLabel, [data-baseweb="tab"], .big-font {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1px;
    }
    
    /* 2. NEON SCROLLBARS */
    ::-webkit-scrollbar { width: 8px; height: 8px; background: #1a001e; }
    ::-webkit-scrollbar-thumb { background: #00FF85; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #00cc6a; }
    ::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); }

    /* 3. GLASSMORPHISM SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: rgba(20, 0, 30, 0.95);
        border-right: 1px solid rgba(0, 255, 133, 0.2);
    }
    section[data-testid="stSidebar"] > div { background-color: transparent; }

    /* 4. CUSTOM NEON INPUT STYLING */
    div[data-baseweb="slider"] div[role="slider"] { background-color: #00FF85 !important; }
    div[data-baseweb="slider"] div[data-testid="stTickBar"] { background: linear-gradient(to right, #00FF85, #00FF85) !important; }
    span[data-baseweb="checkbox"] div[class*="checked"] { background-color: #00FF85 !important; border-color: #00FF85 !important; }
    span[data-baseweb="tag"] { background-color: rgba(0, 255, 133, 0.2) !important; border: 1px solid #00FF85 !important; }
    span[data-baseweb="tag"] span { color: #FFFFFF !important; }

    /* 5. TAB STYLING */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 8px;
        border: 1px solid rgba(0, 255, 133, 0.2);
        gap: 8px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: auto;
        background-color: transparent;
        border: 1px solid transparent;
        color: #AAAAAA;
        font-weight: 700;
        font-size: 0.9rem;
        text-transform: uppercase;
        border-radius: 8px;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { background-color: rgba(255, 255, 255, 0.08); color: #FFFFFF; }
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 255, 133, 0.15) !important;
        color: #00FF85 !important;
        border: 1px solid #00FF85 !important;
        box-shadow: 0 0 15px rgba(0, 255, 133, 0.2);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    /* 6. AESTHETIC PLAYER TABLE (FIXED Z-INDEX ISSUES) */
    .modern-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 8px;
        font-family: 'Roboto', sans-serif;
        color: #E0E0E0;
    }
    
    .modern-table th {
        /* FIX: Solid background matching page theme to prevent "peeping" */
        background-color: #1a001e !important; 
        color: #00FF85;
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        padding: 15px;
        text-align: center;
        border-bottom: 2px solid #00FF85;
        letter-spacing: 1px;
        
        /* FIX: Sticky positioning with EXTREMELY high Z-Index to stay on top */
        position: sticky;
        top: 0;
        z-index: 10000; 
        box-shadow: 0 4px 10px -2px rgba(0,0,0,0.5); /* Shadow to separate header from scrolling content */
    }
    .modern-table th:first-child { text-align: left; padding-left: 20px; }
    
    .modern-table tbody tr {
        transition: all 0.2s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 1; /* Keep rows lower than header */
    }
    .modern-table tbody tr:hover {
        transform: scale(1.005);
        box-shadow: 0 5px 15px rgba(0, 255, 133, 0.15);
        z-index: 10; /* Lift row slightly, but still below header's 10000 */
        position: relative;
    }
    
    .modern-table td {
        padding: 12px;
        vertical-align: middle;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .modern-table td:first-child {
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
    }
    .modern-table td:last-child {
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* IMPROVED FIXTURE PILLS */
    .mini-fix-container {
        display: flex;
        gap: 4px;
        justify-content: center;
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
</style>
""", unsafe_allow_html=True)

# --- 2. LOAD DATA ---
df = db.fetch_main_data()
df = df.fillna(0)

# Calculate Metrics
df['matches_played'] = df['matches_played'].replace(0, 1)
df['minutes'] = df['minutes'].replace(0, 1)
df['avg_minutes'] = df['minutes'] / df['matches_played']
df['xgi_per_90'] = (df['xgi'] / df['minutes']) * 90
df['xgc_per_90'] = (df['xgc'] / df['minutes']) * 90
df['dc_per_90'] = (df['def_cons'] / df['minutes']) * 90
df['tackles_per_90'] = (df['tackles'] / df['minutes']) * 90

ep_map = db.get_expected_points_map()
df['ep_next'] = df['player_id'].map(ep_map).fillna(0.0)

# --- SIDEBAR ---
with st.sidebar:
    if "fpl_metric_logo.png" in [f.name for f in os.scandir(".")]: 
        st.image("fpl_metric_logo.png", use_container_width=True)
    
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
        
        exclude_unavailable = st.checkbox("Exclude Unavailable (Red Flags)", value=False)
        
        max_price = st.slider("Max Price (£)", 3.8, 15.1, 15.1, 0.1)
        max_owner = st.slider("Max Ownership (%)", 0.0, 100.0, 100.0, 0.5)
        
        st.subheader("Performance")
        min_mpg = st.slider("Min Minutes Per Game", 0, 90, 0, 5)
        min_ppg = st.slider("Min Points Per Game", 0.0, 10.0, 0.0, 0.1)
        min_dc90 = st.slider("Min Def. Contributions / 90", 0.0, 15.0, 0.0, 0.5)
        
        submitted = st.form_submit_button("Apply Filters", use_container_width=True)

    st.markdown("---")
    st.markdown("""<a href="https://www.buymeacoffee.com/fplmetric" target="_blank" class="bmc-button"><img src="https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg" alt="Buy me a coffee" class="bmc-logo"><span>Buy me a coffee</span></a>""", unsafe_allow_html=True)

# --- FILTER LOGIC ---
df = df[df['minutes'] >= 90]

if exclude_unavailable:
    df = df[~df['status'].isin(['i', 'u', 'n', 's'])]

filtered = df[
    (df['team_name'].isin(selected_teams)) & 
    (df['position'].isin(position)) &
    (df['cost'] <= max_price) & 
    (df['selected_by_percent'] <= max_owner) &
    (df['avg_minutes'] >= min_mpg) & 
    (df['points_per_game'] >= min_ppg) & 
    (df['dc_per_90'] >= min_dc90)
]

# --- MAIN DISPLAY (CENTERED LOGO) ---
if "fpl_metric_logo.png" in [f.name for f in os.scandir(".")]: 
    col_l, col_m, col_r = st.columns([3, 2, 3]) 
    with col_m: 
        st.image("fpl_metric_logo.png", use_container_width=True)

# =========================================================================
# 📅 DEADLINE & FIXTURES WIDGET
# =========================================================================
gw_name, deadline_iso, fixtures_data = db.get_next_gw_data()

if gw_name and deadline_iso:
    fixtures_json = json.dumps(fixtures_data)
    
    combined_html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@400;700&display=swap');
        .widget-container {{ margin-bottom: 0px; font-family: 'Roboto', sans-serif; }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: #00FF85; border-radius: 3px; }}
        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.2); }}
        .deadline-box {{
            background: linear-gradient(135deg, #1a001e 0%, #37003c 100%);
            border: 1px solid #00FF85; border-top-left-radius: 12px; border-top-right-radius: 12px;
            padding: 15px; text-align: center; color: white; border-bottom: none;
        }}
        .label {{ color: #00FF85; font-size: 0.9rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px; font-family: 'Orbitron', sans-serif; }}
        .timer {{ font-size: 2.2rem; font-weight: 900; margin: 0; line-height: 1.1; font-family: 'Orbitron', sans-serif; }}
        .sub {{ font-size: 0.85rem; color: #BBB; margin-top: 5px; }}
        .fix-container {{
            border: 1px solid #00FF85; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;
            overflow: hidden; background-color: rgba(255, 255, 255, 0.02);
        }}
        .fix-header {{
            background: linear-gradient(90deg, rgba(55,0,60,0.9) 0%, rgba(30,30,30,0.9) 100%);
            padding: 10px 20px; font-weight: 700; color: #00FF85;
            text-align: center; font-family: 'Orbitron', sans-serif;
            border-top: 1px solid rgba(255,255,255,0.1);
            border-bottom: 1px solid #00FF85;
        }}
        .content {{ padding: 20px; }}
        .match-grid {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; }}
        .match-card {{
            background-color: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; padding: 10px; display: flex; justify-content: space-between; align-items: center;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            cursor: pointer;
            flex: 1 1 280px; max-width: 350px;
        }}
        .match-card:hover {{ 
            border-color: #00FF85; background-color: rgba(0, 255, 133, 0.05);
            transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0, 255, 133, 0.2);
        }}
        .team-col {{ display: flex; flex-direction: column; align-items: center; width: 60px; }}
        .team-logo {{ width: 35px; height: 35px; object-fit: contain; margin-bottom: 5px; }}
        .team-name {{ font-size: 0.75rem; font-weight: 700; text-align: center; color: #FFF; }}
        .match-info {{ display: flex; flex-direction: column; align-items: center; color: #AAA; }}
        .match-time {{ font-size: 1rem; font-weight: 700; color: #00FF85; font-family: 'Orbitron', sans-serif; }}
        .match-date {{ font-size: 0.7rem; text-transform: uppercase; }}
    </style>
    
    <div class="widget-container">
        <div class="deadline-box">
            <div class="label">{gw_name} DEADLINE</div>
            <div id="timer" class="timer">Loading...</div>
            <div id="sub" class="sub"></div>
        </div>
        <div class="fix-container">
            <div class="fix-header">View {gw_name} Fixtures (Your Local Time)</div>
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
    n_fixtures = len(fixtures_data)
    n_rows = (n_fixtures + 2) // 3  
    widget_height = 180 + (n_rows * 95) 
    components.html(combined_html, height=widget_height, scrolling=False)
else:
    st.info("No fixtures found for next Gameweek.")

# =========================================================================

# --- TITLE ---
st.markdown("""<div style="text-align: center; margin-bottom: 50px; margin-top: 10px;"><h1 style="font-size: 2.8rem; font-weight: 900; background: linear-gradient(to right, #00FF85, #FFFFFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; font-family: 'Orbitron', sans-serif;">FPL Metric Scouting Dashboard</h1></div>""", unsafe_allow_html=True)

# --- INFO BOX ---
st.markdown(
    """
    <div class="scout-tip">
        <span style="color: #E0E0E0; font-size: 1rem; font-family: 'Roboto', sans-serif;">
            <strong style="color: #00FF85;">SCOUT'S TIP:</strong> 
            Can't find a player? Open the <strong style="color: #fff; text-decoration: underline decoration-color: #00FF85;">Sidebar</strong> to filter by Team, Position, Price, PPG, Mins/Game, and Work Rate.
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- REPLACED METRICS WITH CUSTOM CARDS (NO EMOJIS) ---
col1, col2, col3, col4 = st.columns(4)
if not filtered.empty:
    best_xgi = filtered.sort_values('xgi', ascending=False).iloc[0]
    best_dc = filtered.sort_values('dc_per_90', ascending=False).iloc[0]
    best_val = filtered.sort_values('value_season', ascending=False).iloc[0]
    best_ppg = filtered.sort_values('points_per_game', ascending=False).iloc[0]

    def metric_card(title, name, value, icon):
        return f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
            border: 1px solid rgba(0, 255, 133, 0.4);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            height: 100%;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        " onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 5px 15px rgba(0, 255, 133, 0.2)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)';">
            <div style="font-size: 1.5rem; margin-bottom: 5px;">{icon}</div>
            <div style="color: #AAAAAA; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-family: 'Orbitron', sans-serif;">{title}</div>
            <div style="color: #FFFFFF; font-size: 1.2rem; font-weight: 900; line-height: 1.2;">{name}</div>
            <div style="background-color: rgba(0, 255, 133, 0.15); color: #00FF85; padding: 4px 12px; border-radius: 12px; font-size: 0.9rem; font-weight: bold; margin-top: 8px; border: 1px solid rgba(0, 255, 133, 0.3);">
                {value}
            </div>
        </div>
        """

    with col1: st.markdown(metric_card("Threat King (xGI)", best_xgi['web_name'], f"{best_xgi['xgi']}", ""), unsafe_allow_html=True)
    with col2: st.markdown(metric_card("Work Rate (DC/90)", best_dc['web_name'], f"{best_dc['dc_per_90']:.2f}", ""), unsafe_allow_html=True)
    with col3: st.markdown(metric_card("Best Value", best_val['web_name'], f"{best_val['value_season']}", ""), unsafe_allow_html=True)
    with col4: st.markdown(metric_card("Best PPG", best_ppg['web_name'], f"{best_ppg['points_per_game']}", ""), unsafe_allow_html=True)

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
    team_map = db.get_team_map()
    team_fixtures = db.get_team_upcoming_fixtures()
    
    base_headers = ["Player", "Next 5", "Price", "Own%", "Matches"]
    dynamic_headers = list(column_config.values())
    all_headers = base_headers + dynamic_headers
    header_html = "".join([f"<th>{h}</th>" for h in all_headers])
    
    # IMPROVED CONTRAST FOR PILLS
    fdr_colors = {1: '#375523', 2: '#00FF85', 3: '#EBEBEB', 4: '#FF0055', 5: '#680808'}
    fdr_text = {1: 'white', 2: 'black', 3: 'black', 4: 'white', 5: 'white'}
    
    html_rows = ""
    for _, row in sorted_df.iterrows():
        t_code = team_map.get(row['team_name'], 0)
        logo_img = f"https://resources.premierleague.com/premierleague/badges/20/t{t_code}.png"
        
        status = row['status']
        row_style = ""
        border_color = "rgba(255, 255, 255, 0.05)"
        
        # RESTORED FULL ROW HIGHLIGHT + BORDER
        if status in ['i', 'u', 'n', 's']: 
            row_style = 'background-color: rgba(255, 0, 85, 0.15);' # Red tint
            border_color = "#FF0055"
        elif status == 'd': 
            row_style = 'background-color: rgba(255, 204, 0, 0.15);' # Yellow tint
            border_color = "#FFCC00"
        else:
            row_style = 'background-color: rgba(255, 255, 255, 0.03);' # Default dark
            
        status_dot = '<span class="status-pill" style="background-color: #00FF85;"></span>'
        if status in ['i', 'u', 'n', 's']: status_dot = '<span class="status-pill" style="background-color: #FF0055;"></span>'
        elif status == 'd': status_dot = '<span class="status-pill" style="background-color: #FFCC00;"></span>'
        
        # Combined styles: Background tint + Neon Border
        html_rows += f"""<tr style="{row_style} border-left: 4px solid {border_color};">
        <td style="padding-left: 20px;"><div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 10px;">{status_dot}</div><img src="{logo_img}" style="width: 35px;">
            <div style="display: flex; flex-direction: column;"><span style="font-weight: bold; color: #FFF;">{row['web_name']}</span><span style="font-size: 0.8rem; color: #AAA;">{row['team_name']} | {row['position']}</span></div>
        </div></td>"""
        
        my_fixtures = team_fixtures.get(row['team_name'], [])
        fix_html = '<div class="mini-fix-container">'
        for f in my_fixtures:
            bg, txt = fdr_colors.get(f['diff'], '#333'), fdr_text.get(f['diff'], 'white')
            # Added min-width and centered text for visibility
            fix_html += f'<div class="mini-fix-box" style="background-color: {bg}; color: {txt}; min-width: 38px; text-align: center;">{f["opp"]}</div>'
        fix_html += '</div>'
        html_rows += f'<td style="text-align: center;">{fix_html}</td>'
        
        for col_name in ['cost', 'selected_by_percent', 'matches_played'] + list(column_config.keys()):
            val = row[col_name]
            if isinstance(val, float): val = f"{val:.2f}"
            if col_name == 'cost': val = f"£{float(val):.1f}"
            elif col_name == 'selected_by_percent': val = f"{val}%"
            elif col_name in ['matches_played', 'avg_minutes', 'total_points', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded']: val = int(float(val))
            
            style = "text-align: center;"
            if col_name == selected_col: style += " font-weight: bold; color: #00FF85;"
            html_rows += f"""<td style="{style}">{val}</td>"""
        html_rows += "</tr>"

    st.markdown(f"""<div class="player-table-container"><table class="modern-table"><thead><tr>{header_html}</tr></thead><tbody>{html_rows}</tbody></table></div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Attack", "Defense", "Work Rate"])
with tab1: render_modern_table(filtered, { "ep_next": "XP", "total_points": "Pts", "points_per_game": "PPG", "avg_minutes": "Mins/Gm", "news": "News" }, "sort_ov")
with tab2: render_modern_table(filtered, { "xg": "xG", "xa": "xA", "xgi": "xGI", "xgi_per_90": "xGI/90", "goals_scored": "Goals", "assists": "Assists" }, "sort_att")
with tab3: render_modern_table(filtered, { "clean_sheets": "Clean Sheets", "goals_conceded": "Conceded", "xgc": "xGC", "xgc_per_90": "xGC/90" }, "sort_def")
with tab4: render_modern_table(filtered, { "def_cons": "Total DC", "dc_per_90": "DC/90", "tackles": "Tackles", "tackles_per_90": "Tackles/90", "cbi": "CBI" }, "sort_wr")

st.markdown("---") 
st.header("Fixture Difficulty Ticker")
current_next_gw = db.get_next_gameweek_id()
horizon_opts = ["Next 3 GWs", "Next 5 GWs"] + [f"GW {current_next_gw+i}" for i in range(5)]
c1, c2, c3 = st.columns(3)
with c1: s_order = st.selectbox("Sort Order", ["Easiest", "Hardest", "Alphabetical"])
with c2: v_type = st.selectbox("Type", ["Overall", "Attack", "Defence"])
with c3: horizon = st.selectbox("Horizon", horizon_opts)

if horizon == "Next 3 GWs": s_gw, e_gw = current_next_gw, current_next_gw + 2
elif horizon == "Next 5 GWs": s_gw, e_gw = current_next_gw, current_next_gw + 4
else: s_gw = e_gw = int(horizon.split(" ")[1])

t_df = db.get_fixture_ticker(s_gw, e_gw)
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
df_c = db.get_db_price_changes()
if df_c.empty: st.info("No price changes detected.")
else:
    c_r, c_f = st.columns(2)
    # --- ARROW FIX: FILLED CIRCLES (Green/Black & Pink/White) ---
    icon_up = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="12" fill="#00FF85"/><path d="M7 14L12 9L17 14" stroke="black" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    icon_dn = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="12" fill="#FF0055"/><path d="M7 10L12 15L17 10" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    
    with c_r:
        st.subheader("Price Risers")
        risers = df_c[df_c['change'] > 0].sort_values('change', ascending=False)
        if risers.empty: st.info("No risers.")
        else:
            h_r = ""
            for _, r in risers.iterrows():
                tc = db.get_team_map().get(r['team'], 0)
                # +£ FIX & 1 Decimal
                h_r += f"""<tr><td style="padding-left: 20px;"><div style="display: flex; align-items: center; gap: 10px;">{icon_up}<img src="https://resources.premierleague.com/premierleague/badges/20/t{tc}.png" style="width: 30px;"><div><b>{r['web_name']}</b><br><span style="font-size:0.8rem; color:#AAA;">{r['team']}</span></div></div></td><td style="text-align: center;">£{r['cost']:.1f}</td><td style="text-align: center; color: #00FF85;">+£{r['change']:.1f}</td></tr>"""
            st.markdown(f"""<div class="player-table-container"><table class="modern-table"><thead><tr><th>Player</th><th>Price</th><th>Change</th></tr></thead><tbody>{h_r}</tbody></table></div>""", unsafe_allow_html=True)
            
    with c_f:
        st.subheader("Price Fallers")
        fallers = df_c[df_c['change'] < 0].sort_values('change')
        if fallers.empty: st.info("No fallers.")
        else:
            h_f = ""
            for _, r in fallers.iterrows():
                tc = db.get_team_map().get(r['team'], 0)
                # -£ FIX (ABS Value) & 1 Decimal
                h_f += f"""<tr><td style="padding-left: 20px;"><div style="display: flex; align-items: center; gap: 10px;">{icon_dn}<img src="https://resources.premierleague.com/premierleague/badges/20/t{tc}.png" style="width: 30px;"><div><b>{r['web_name']}</b><br><span style="font-size:0.8rem; color:#AAA;">{r['team']}</span></div></div></td><td style="text-align: center;">£{r['cost']:.1f}</td><td style="text-align: center; color: #FF0055;">-£{abs(r['change']):.1f}</td></tr>"""
            st.markdown(f"""<div class="player-table-container"><table class="modern-table"><thead><tr><th>Player</th><th>Price</th><th>Change</th></tr></thead><tbody>{h_f}</tbody></table></div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""<div style='text-align: center; color: #B0B0B0;'><p><strong>FPL Metric</strong> | Built for the FPL Community</p><p><a href="https://x.com/FPL_Metric" target="_blank" style="color: #00FF85; text-decoration: none;">Follow on X: @FPL_Metric</a></p></div>""", unsafe_allow_html=True)
