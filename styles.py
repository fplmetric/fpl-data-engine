GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');

/* GLOBAL RESET */
span[data-baseweb="tag"] { color: black !important; font-weight: bold; }
div[data-baseweb="select"] > div { cursor: pointer !important; }

/* FIX: Increase top padding so Logo isn't cut off */
.block-container { padding-top: 3rem !important; padding-bottom: 2rem !important; }

/* --- LOGO FIXES --- */

/* 1. Sidebar Logo: Center it and give it proper sizing */
section[data-testid="stSidebar"] div[data-testid="stImage"] {
    text-align: center; /* Centers the container */
    display: block;
    margin-left: auto;
    margin-right: auto;
}

section[data-testid="stSidebar"] div[data-testid="stImage"] img {
    object-fit: contain !important;
    width: 80% !important; /* Slightly smaller than full width looks better in sidebar */
    max-height: 120px !important; /* Increased height so it's not tiny */
    margin: 0 auto !important;
}

/* 2. Main View Logo: Full visibility, no cropping */
div[data-testid="stAppViewContainer"] div[data-testid="stImage"] img {
    object-fit: contain !important;
    width: 100% !important;
    height: auto !important; 
    margin: 0 auto;
    display: block;
}

/* TABS */
div[data-baseweb="tab-list"] { gap: 8px; margin-bottom: 10px; }
button[data-baseweb="tab"] {
    font-size: 0.9rem !important; font-weight: 600 !important; padding: 6px 18px !important;
    background-color: transparent !important; border-radius: 30px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important; color: #CCC !important; transition: all 0.3s ease;
}
button[data-baseweb="tab"]:hover {
    background-color: rgba(255, 255, 255, 0.05) !important; border-color: #FFF !important; color: #FFF !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #37003c !important; color: #00FF85 !important;
    border: 1px solid #00FF85 !important; box-shadow: 0 0 15px rgba(0, 255, 133, 0.15);
}

/* TABLES */
.player-table-container {
    max-height: 550px; 
    overflow-y: auto; 
    overflow-x: auto;
    border: 1px solid #444; 
    border-radius: 8px; 
    margin-bottom: 15px; 
    background-color: transparent;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}
.fixture-table-container {
    width: 100%;
    border: 1px solid #444; 
    border-radius: 8px; 
    overflow-x: auto; 
    margin-bottom: 15px; 
    background-color: transparent;
}

/* MODERN TABLE STYLE */
.modern-table { width: 100%; border-collapse: separate; border-spacing: 0; font-family: 'Roboto', sans-serif; }
.modern-table th {
    background: linear-gradient(to bottom, #5e0066, #37003c); color: #ffffff; padding: 12px 10px;
    text-align: center !important; font-weight: 700; font-size: 0.85rem; text-transform: uppercase;
    border-bottom: none; border-top: 1px solid rgba(255,255,255,0.1); position: sticky; top: 0; z-index: 10;
}
.modern-table th:first-child { text-align: left !important; padding-left: 20px !important; border-top-left-radius: 8px; }
.modern-table th:last-child { border-top-right-radius: 8px; }
.modern-table td {
    padding: 10px 10px; border-bottom: 1px solid #2c2c2c; color: #E0E0E0; vertical-align: middle; font-size: 0.9rem;
}
.modern-table tr:hover td { background-color: rgba(255, 255, 255, 0.07); }

.status-pill { display: inline-block; width: 8px; height: 8px; border-radius: 50%; box-shadow: 0 0 5px rgba(0,0,0,0.5); }
.diff-badge { display: block; padding: 6px 4px; border-radius: 6px; text-align: center; font-weight: bold; font-size: 0.85rem; width: 100%; }
.mini-fix-container { display: flex; gap: 4px; justify-content: center; }
.mini-fix-box {
    width: 32px; height: 20px; display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 800; border-radius: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

/* SCOUT TIP BOX */
.scout-tip {
    background: linear-gradient(90deg, rgba(55,0,60,0.9) 0%, rgba(30,30,30,0.9) 100%);
    border: 1px solid #00FF85; border-radius: 8px; padding: 10px 15px;
    margin-bottom: 20px; display: flex; align-items: center;
    box-shadow: 0 4px 10px rgba(0, 255, 133, 0.1);
}

/* BMC BUTTON */
.bmc-button {
    display: flex; align-items: center; justify-content: center; background-color: #FFDD00;
    color: #000000 !important; font-weight: 700; padding: 10px 20px; border-radius: 30px;
    margin-top: 20px; text-decoration: none; border: 2px solid #000; transition: transform 0.2s;
}
.bmc-button:hover { transform: translateY(-2px); text-decoration: none; }
.bmc-logo { width: 20px; height: 20px; margin-right: 8px; }

@media (max-width: 768px) { h1 { font-size: 1.8rem !important; } }
</style>
"""
