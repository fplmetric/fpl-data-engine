# styles.py

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');

/* GLOBAL */
span[data-baseweb="tag"] { color: black !important; font-weight: bold; }
div[data-baseweb="select"] > div { cursor: pointer !important; }

/* TABS */
div[data-baseweb="tab-list"] { gap: 8px; margin-bottom: 15px; }
button[data-baseweb="tab"] {
    font-size: 1rem !important; font-weight: 600 !important; padding: 8px 20px !important;
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

/* TABLES (Scrollable Fixed Height) */
.player-table-container {
    max-height: 550px; 
    overflow-y: auto; 
    overflow-x: auto;
    border: 1px solid #444; 
    border-radius: 8px; 
    margin-bottom: 20px; 
    background-color: transparent;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}
.fixture-table-container {
    width: 100%;
    border: 1px solid #444; 
    border-radius: 8px; 
    overflow-x: auto; 
    margin-bottom: 20px; 
    background-color: transparent;
}

/* MODERN TABLE STYLE */
.modern-table { width: 100%; border-collapse: separate; border-spacing: 0; font-family: 'Roboto', sans-serif; }
.modern-table th {
    background: linear-gradient(to bottom, #5e0066, #37003c); color: #ffffff; padding: 16px 12px;
    text-align: center !important; font-weight: 700; font-size: 0.85rem; text-transform: uppercase;
    border-bottom: none; border-top: 1px solid rgba(255,255,255,0.1); position: sticky; top: 0; z-index: 10;
}
.modern-table th:first-child { text-align: left !important; padding-left: 20px !important; border-top-left-radius: 8px; }
.modern-table th:last-child { border-top-right-radius: 8px; }
.modern-table td {
    padding: 12px 12px; border-bottom: 1px solid #2c2c2c; color: #E0E0E0; vertical-align: middle; font-size: 0.9rem;
}
.modern-table tr:hover td { background-color: rgba(255, 255, 255, 0.07) !important; }

.status-pill { display: inline-block; width: 8px; height: 8px; border-radius: 50%; box-shadow: 0 0 5px rgba(0,0,0,0.5); }
.diff-badge { display: block; padding: 8px 6px; border-radius: 6px; text-align: center; font-weight: bold; font-size: 0.9rem; width: 100%; }
.mini-fix-container { display: flex; gap: 4px; justify-content: center; }
.mini-fix-box {
    width: 32px; height: 22px; display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 800; border-radius: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

/* MATCH CARDS */
.match-grid { 
    display: grid; 
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
    gap: 15px; 
    margin-top: 15px; 
}
.match-card {
    background-color: rgba(255,255,255,0.03); 
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px; 
    padding: 15px; 
    display: flex; 
    justify-content: space-between; 
    align-items: center;
    transition: transform 0.2s, background-color 0.2s;
}
.match-card:hover { 
    background-color: rgba(255,255,255,0.08); 
    transform: translateY(-2px); 
    border-color: #00FF85; 
}
.team-col { display: flex; flex-direction: column; align-items: center; width: 80px; }
.team-logo { width: 45px; height: 45px; object-fit: contain; margin-bottom: 8px; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.5)); }
.team-name { font-size: 0.85rem; font-weight: 700; text-align: center; color: #FFF; line-height: 1.1; }
.match-info { display: flex; flex-direction: column; align-items: center; color: #AAA; }
.match-time { font-size: 1.1rem; font-weight: 700; color: #00FF85; margin-bottom: 2px; }
.match-date { font-size: 0.75rem; text-transform: uppercase; }

/* SCOUT TIP BOX */
.scout-tip {
    background: linear-gradient(90deg, rgba(55,0,60,0.9) 0%, rgba(30,30,30,0.9) 100%);
    border: 1px solid #00FF85; border-radius: 8px; padding: 12px 20px;
    margin-bottom: 25px; display: flex; align-items: center;
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
