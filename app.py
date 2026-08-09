import streamlit as st
import sys
import os
import sqlite3
import pandas as pd
from datetime import date, datetime

sys.path.append(os.path.abspath("core"))
from database import init_db, get_connection, release_connection

# Import your tools
from tools import mobilis_rn_tool
from tools import ota_odr_tool
from tools import oa_return_tool
from tools import lift_crane_tool
from tools import dispatch_tool
from tools import leader_portal
from tools import driver_portal

# --- PAGE CONFIG ---
st.set_page_config(page_title="ATLCOM Management", page_icon="favicon.ico", layout="wide", initial_sidebar_state="collapsed")

# --- COMPREHENSIVE TRANSLATIONS DICTIONARY ---
translations = {
    'EN': {
        'title': "ATLCOM", 'settings': "Settings", 'language': "Language", 'theme': "Theme",
        'menu_dashboard': "🏠 Dashboard", 'menu_dispatch': "📡 Dispatch", 'menu_materials': "📦 Materials", 'menu_tools': "🛠️ Tools",
        'welcome': "Welcome to your centralized project management workspace.",
        'active_clients': "Active Clients", 'total_inventory': "Total Inventory Items", 'total_teams': "Total Teams",
        'team_status': "Team Live Status", 'working_teams': "Working Teams", 'available_teams': "Available Teams", 'resting_teams': "Resting Teams",
        'select_client': "1. Select Client", 'select_tool': "2. Select Tool", 'client_label': "Client",
        'tab_mob': "Mobilis (ATM)", 'tab_ota': "Djezzy (OTA)", 'tab_oa': "Ooredoo (OA)", 'tab_lc': "Lift & Crane",
        'add_new': "➕ Add New Material", 'add_new_item': "➕ Add New Item", 'part_number': "Part Number",
        'mat_name': "Material Name *", 'nature': "Nature", 'submit': "Submit", 'designation': "Désignation *",
        'pn': "PN", 'oa_info': "OA list builds itself automatically in the OA Return Tool!",
        'item_code': "Item Code", 'item_name': "Item Name *", 'item_by': "Item By (Unit)",
    },
    'FR': {
        'title': "ATLCOM", 'settings': "Paramètres", 'language': "Langue", 'theme': "Thème",
        'menu_dashboard': "🏠 Tableau de bord", 'menu_dispatch': "📡 Dispatch", 'menu_materials': "📦 Matériel", 'menu_tools': "🛠️ Outils",
        'welcome': "Bienvenue dans votre espace de gestion de projet centralisé.",
        'active_clients': "Clients Actifs", 'total_inventory': "Total des Articles", 'total_teams': "Nombre d'Équipes",
        'team_status': "Statut des Équipes", 'working_teams': "En Travail", 'available_teams': "Disponibles", 'resting_teams': "En Repos",
        'select_client': "1. Sélectionner Client", 'select_tool': "2. Sélectionner Outil", 'client_label': "Client",
        'tab_mob': "Mobilis (ATM)", 'tab_ota': "Djezzy (OTA)", 'tab_oa': "Ooredoo (OA)", 'tab_lc': "Levage & Grue",
        'add_new': "➕ Ajouter Matériel", 'add_new_item': "➕ Ajouter Article", 'part_number': "Numéro de Pièce",
        'mat_name': "Nom du Matériel *", 'nature': "Nature", 'submit': "Valider", 'designation': "Désignation *",
        'pn': "PN", 'oa_info': "La liste OA se construit automatiquement dans l'outil de retour OA !",
        'item_code': "Code Article", 'item_name': "Nom de l'Article *", 'item_by': "Unité",
    },
    'AR': {
        'title': "ATLCOM", 'settings': "إعدادات", 'language': "اللغة", 'theme': "المظهر",
        'menu_dashboard': "🏠 لوحة التحكم", 'menu_dispatch': "📡 التتبع", 'menu_materials': "📦 المواد", 'menu_tools': "🛠️ الأدوات",
        'welcome': "مرحباً بك في مساحة عمل إدارة المشاريع المركزية.",
        'active_clients': "العملاء النشطون", 'total_inventory': "إجمالي العناصر", 'total_teams': "إجمالي الفرق",
        'team_status': "حالة الفرق", 'working_teams': "عاملة", 'available_teams': "متاحة", 'resting_teams': "في راحة",
        'select_client': "1. اختر العميل", 'select_tool': "2. اختر الأداة", 'client_label': "العميل",
        'tab_mob': "موبيليس (ATM)", 'tab_ota': "جازي (OTA)", 'tab_oa': "أوريدو (OA)", 'tab_lc': "الرافعات والونش",
        'add_new': "➕ إضافة مادة", 'add_new_item': "➕ إضافة عنصر", 'part_number': "رقم القطعة",
        'mat_name': "اسم المادة *", 'nature': "الطبيعة", 'submit': "تأكيد", 'designation': "التسمية *",
        'pn': "PN", 'oa_info': "تُبنى قائمة OA تلقائياً في أداة إرجاع OA!",
        'item_code': "رمز العنصر", 'item_name': "اسم العنصر *", 'item_by': "الوحدة",
    }
}

# --- SESSION STATE INIT ---
if 'lang' not in st.session_state: st.session_state.lang = 'EN'
if 'theme' not in st.session_state: st.session_state.theme = 'Light'

t = translations[st.session_state.lang]

# --- DYNAMIC CSS (ULTRA PREMIUM GLASSMORPHISM & TOP HEADER) ---
def get_css():
    is_dark = st.session_state.theme == 'Dark'
    is_ar = st.session_state.lang == 'AR'
    
    if is_dark:
        body_bg = "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
        glass_bg = "rgba(30, 41, 59, 0.6)"
        glass_border = "rgba(255, 255, 255, 0.1)"
        text_color = "#f1f5f9"
        card_title_color = "#94a3b8"
        input_bg = "rgba(15, 23, 42, 0.5)"
        df_bg = "rgba(15, 23, 42, 0.8)"
        login_bg = "rgba(30, 41, 59, 0.45)"
        login_input_bg = "rgba(15, 23, 42, 0.6)"
    else:
        body_bg = "linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)"
        glass_bg = "rgba(255, 255, 255, 0.65)"
        glass_border = "rgba(255, 255, 255, 0.9)"
        text_color = "#1e293b"
        card_title_color = "#64748b"
        input_bg = "rgba(255, 255, 255, 0.5)"
        df_bg = "rgba(255, 255, 255, 0.8)"
        login_bg = "rgba(255, 255, 255, 0.45)"
        login_input_bg = "rgba(255, 255, 255, 0.6)"
        
    direction = "rtl" if is_ar else "ltr"
    text_align = "right" if is_ar else "left"
    
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #0078D7; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #0056b3; }}

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            direction: {direction};
            text-align: {text_align};
        }}
        .stApp {{
            background: {body_bg} !important;
            color: {text_color} !important;
        }}
        
        /* Completely Hide Default Streamlit Sidebar & Buttons */
        section[data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"], #MainMenu, footer {{ display: none !important; }}
        
        /* Typography */
        .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{ color: {text_color} !important; }}
        .block-container {{ padding-top: 6rem !important; padding-bottom: 3rem; max-width: 1200px; margin: 0 auto; }}
        
        /* ==========================================
           PREMIUM GLASS TOP HEADER
           ========================================== */
        .top-header {{
            position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
            background: {glass_bg} !important;
            backdrop-filter: blur(16px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
            border-bottom: 1px solid {glass_border} !important;
            padding: 10px 20px;
            display: flex; align-items: center; justify-content: space-between;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
        }}
        .header-logo {{ font-size: 20px; font-weight: 800; color: #0078D7; display: flex; align-items: center; gap: 10px; }}
        
        /* Navigation Pills inside Header */
        .top-header [data-testid="stRadio"] > div {{ flex-direction: row !important; display: flex !important; gap: 8px !important; background: transparent !important; }}
        .top-header [data-testid="stRadio"] > div > label {{
            background: {input_bg} !important; border: 1px solid {glass_border} !important;
            padding: 8px 16px !important; border-radius: 10px !important;
            transition: all 0.2s ease !important; cursor: pointer !important;
            font-weight: 500 !important;
        }}
        .top-header [data-testid="stRadio"] > div > label:hover {{ background: {glass_bg} !important; }}
        .top-header [data-testid="stRadio"] > div > label[data-checked="true"] {{
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
            color: white !important; border-color: transparent !important;
            box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3) !important;
        }}
        .top-header [data-testid="stRadio"] > div > label > div:first-child {{ display: none !important; }}
        .top-header [data-testid="stRadio"] > div > label > div:last-child {{ width: 100% !important; font-size: 14px !important; font-weight: 600 !important; text-align: center !important; }}
        
        /* Buttons */
        .stButton > button, .stFormSubmitButton > button {{
            color: #ffffff !important; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
            border: none !important; border-radius: 8px !important; font-weight: 600 !important;
            transition: all 0.3s ease !important; box-shadow: 0 4px 6px rgba(79, 172, 254, 0.2) !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            transform: translateY(-2px) !important; box-shadow: 0 6px 12px rgba(79, 172, 254, 0.4) !important;
        }}
        
        /* Dashboard Cards */
        div.card {{
            background-color: {glass_bg} !important; backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important; padding: 25px; border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important; border: 1px solid {glass_border} !important;
            margin-bottom: 15px; border-left: 4px solid #4facfe !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        div.card:hover {{ transform: translateY(-5px); box-shadow: 0 12px 40px rgba(79, 172, 254, 0.2) !important; }}
        .card-title {{ font-size: 14px; color: {card_title_color}; font-weight: 500; margin-bottom: 5px; }}
        .card-value {{ font-size: 32px; font-weight: 800; color: {text_color}; }}
        
        /* Open Tasks Button styled as Glass Card */
        button[k="open_tasks_btn"] {{
            background-color: {glass_bg} !important; backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important; border: 1px solid {glass_border} !important;
            border-left: 4px solid #dc3545 !important; border-radius: 16px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important; color: {text_color} !important;
            height: 100% !important; min-height: 110px !important; display: flex !important;
            flex-direction: column !important; justify-content: center !important; align-items: flex-start !important;
            text-align: left !important; font-weight: 700 !important; transition: transform 0.3s ease, box-shadow 0.3s ease !important;
            margin-bottom: 15px !important;
        }}
        button[k="open_tasks_btn"]:hover {{ transform: translateY(-5px) !important; box-shadow: 0 12px 40px rgba(220, 53, 69, 0.2) !important; background: {glass_bg} !important; }}
        
        /* Inputs & DataFrames (Flawless Text Visibility) */
        .stTextInput > div > div, .stSelectbox > div > div > div {{
            background-color: {input_bg} !important; backdrop-filter: blur(4px) !important;
            border: 1px solid {glass_border} !important; border-radius: 8px !important;
        }}
        .stTextInput > div > div input, .stSelectbox > div > div > div {{ color: {text_color} !important; }}
        .stTextInput > div > div input::placeholder {{ color: {card_title_color} !important; opacity: 0.8 !important; }}
        .stTextInput > div > div:focus-within, .stSelectbox > div > div > div:focus-within {{ border-color: #4facfe !important; box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.2) !important; }}
        .stDataFrame {{ background-color: {df_bg} !important; backdrop-filter: blur(8px) !important; border: 1px solid {glass_border} !important; border-radius: 12px !important; padding: 10px !important; }}
        div[data-testid="stDataFrame"] div, div[data-testid="stTable"] div {{ color: {text_color} !important; }}
        
        /* ==========================================
           ULTRA PREMIUM LOGIN UI (PERFECT CENTER)
           ========================================== */
        .login-card {{ 
            background: {login_bg} !important; backdrop-filter: blur(24px) saturate(180%) !important; 
            -webkit-backdrop-filter: blur(24px) saturate(180%) !important; padding: 50px 40px !important; 
            border-radius: 28px !important; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15), 0 0 0 1px {glass_border} inset !important; 
            width: 100% !important; max-width: 440px !important; margin: 10vh auto 0 auto !important; 
            text-align: center !important;
            display: flex !important; flex-direction: column !important; align-items: center !important; border: none !important;
        }}
        .login-icon-wrapper {{ width: 90px; height: 90px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 28px; margin: 0 auto 25px auto; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 25px rgba(79, 172, 254, 0.4); }}
        .login-icon {{ font-size: 45px; }}
        
        .login-card [data-testid="stRadio"] > div {{ flex-direction: row !important; display: flex !important; gap: 12px !important; background: transparent !important; width: 100% !important; }}
        .login-card [data-testid="stRadio"] > div > label {{
            background: {login_input_bg} !important; border: 1px solid {glass_border} !important; padding: 15px 10px !important;
            border-radius: 14px !important; flex: 1 !important; text-align: center !important; cursor: pointer !important;
            transition: all 0.3s ease !important; display: flex !important; justify-content: center !important; align-items: center !important; backdrop-filter: blur(4px) !important;
        }}
        .login-card [data-testid="stRadio"] > div > label:hover {{ background: {glass_bg} !important; transform: translateY(-2px) !important; }}
        .login-card [data-testid="stRadio"] > div > label[data-checked="true"] {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important; color: white !important; border-color: transparent !important; box-shadow: 0 6px 18px rgba(79, 172, 254, 0.35) !important; }}
        .login-card [data-testid="stRadio"] > div > label > div:first-child {{ display: none !important; }}
        .login-card [data-testid="stRadio"] > div > label > div:last-child {{ width: 100% !important; font-size: 15px !important; font-weight: 700 !important; }}
        
        .login-card .stTextInput > div > div {{ background: {login_input_bg} !important; border: 1px solid {glass_border} !important; border-radius: 12px !important; padding: 10px 15px !important; box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important; }}
        .login-card .stTextInput > div > div input {{ color: {text_color} !important; }}
        .login-card .stTextInput > div > div input::placeholder {{ color: {card_title_color} !important; opacity: 0.8 !important; }}
        .login-card .stTextInput > div > div:focus-within {{ border-color: #4facfe !important; box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.2) !important; }}
        
        .login-card .stButton {{ width: 100%; display: flex; justify-content: center; margin-top: 10px; }}
        .login-card .stButton > button {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important; border: none !important; padding: 14px 0 !important; border-radius: 12px !important; font-size: 16px !important; font-weight: 700 !important; box-shadow: 0 8px 20px rgba(79, 172, 254, 0.3) !important; }}
        .login-card .stButton > button:hover {{ transform: translateY(-3px) !important; box-shadow: 0 12px 28px rgba(79, 172, 254, 0.45) !important; }}
        
        @media only screen and (max-width: 768px) {{
            .top-header {{ flex-direction: column; gap: 10px; padding: 10px; }}
            .block-container {{ padding-top: 12rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100% !important; }}
            [data-testid="stHorizontalBlock"] {{ flex-direction: column !important; width: 100% !important; align-items: center !important; gap: 10px !important; }}
            .login-card {{ margin-top: 2vh !important; padding: 30px 20px !important; }}
            .login-card [data-testid="stRadio"] > div {{ flex-direction: column !important; }}
        }}
    </style>
    """

st.markdown(get_css(), unsafe_allow_html=True)

init_db()

# --- UNIFIED SESSION INIT FROM URL ---
def init_session():
    params = st.query_params
    if 'role' in params:
        if params['role'] == 'manager':
            st.session_state.manager_logged_in = True
            st.session_state.role = 'manager'
        elif params['role'] == 'leader' and 'lid' in params:
            if 'leader_logged_in' not in st.session_state:
                conn = get_connection()
                df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=%(lid)s", conn, params={"lid": params['lid']})
                release_connection(conn)
                if not df.empty:
                    st.session_state.leader_logged_in = True
                    st.session_state.leader_data = df.iloc[0].to_dict()
                    st.session_state.role = 'leader'
        elif params['role'] == 'driver' and 'driver' in params:
            st.session_state.driver_logged_in = True
            st.session_state.driver_name = params['driver']
            st.session_state.role = 'driver'

init_session()

# --- ROUTING ---
if st.session_state.get('role') == 'leader':
    leader_portal.render_portal()
    st.stop()
elif st.session_state.get('role') == 'driver':
    driver_portal.render_portal()
    st.stop()
elif not st.session_state.get('manager_logged_in'):
    # --- ULTRA PREMIUM LOGIN PAGE (Centered natively) ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='login-icon-wrapper'><span class='login-icon'>🛠️</span></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='font-weight: 800; margin-bottom: 5px;'>ATLCOM</h1>", unsafe_allow_html=True)
        st.markdown("<p style='opacity: 0.7; margin-bottom: 30px;'>Management Portal</p>", unsafe_allow_html=True)
        
        role = st.radio("Select Role", ["Manager", "Team Leader", "Driver"], horizontal=True)
        
        if role == "Manager":
            pwd = st.text_input("Password", type="password")
            if st.button("Login", type="primary", use_container_width=True):
                if pwd == "admin1":
                    st.session_state.manager_logged_in = True
                    st.session_state.role = 'manager'
                    st.query_params['role'] = 'manager'
                    st.rerun()
                else:
                    st.error("Incorrect password")
        elif role == "Team Leader":
            lid = st.text_input("Leader ID")
            if st.button("Login", type="primary", use_container_width=True):
                conn = get_connection()
                df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=%(lid)s", conn, params={"lid": lid})
                release_connection(conn)
                if not df.empty:
                    st.session_state.leader_logged_in = True
                    st.session_state.role = 'leader'
                    st.session_state.leader_data = df.iloc[0].to_dict()
                    st.query_params['role'] = 'leader'
                    st.query_params['lid'] = lid
                    st.rerun()
                else:
                    st.error("Invalid Leader ID")
        elif role == "Driver":
            dname = st.text_input("Driver Name")
            if st.button("Login", type="primary", use_container_width=True):
                st.session_state.driver_logged_in = True
                st.session_state.role = 'driver'
                st.session_state.driver_name = dname
                st.query_params['role'] = 'driver'
                st.query_params['driver'] = dname
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# MANAGER APP STARTS HERE
# ==========================================
TOOL_HIERARCHY = {
    "Mobilis": {
        "📄 RN Filler": mobilis_rn_tool.render_tool,
        "🏗️ LIFT & CRANE Tracker": lift_crane_tool.render_tool
    },
    "Djezzy": {
        "📋 ODR Filler": ota_odr_tool.render_tool,
        "🏗️ LIFT & CRANE Tracker": lift_crane_tool.render_tool
    },
    "Ooredoo": {
        "📤 Return Filler": oa_return_tool.render_tool,
        "🏗️ LIFT & CRANE Tracker": lift_crane_tool.render_tool
    }
}

# --- PREMIUM GLASS TOP HEADER ---
st.markdown("<div class='top-header'>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    st.markdown("<div class='header-logo'>🛠️ ATLCOM</div>", unsafe_allow_html=True)

with col2:
    main_menu = st.radio("Menu", [t['menu_dashboard'], t['menu_dispatch'], t['menu_materials'], t['menu_tools']], horizontal=True, label_visibility="collapsed", key="top_nav")

with col3:
    c_lang, c_theme, c_out = st.columns(3)
    with c_lang:
        lang = st.selectbox("Lang", ['EN', 'FR', 'AR'], key='lang_select', label_visibility="collapsed")
        if lang != st.session_state.lang:
            st.session_state.lang = lang
            st.rerun()
    with c_theme:
        theme = st.selectbox("Theme", ['Light', 'Dark'], key='theme_select', label_visibility="collapsed")
        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.rerun()
    with c_out:
        if st.button("Logout", key="logout_btn", use_container_width=True):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 1. DASHBOARD
# ==========================================
if main_menu == t['menu_dashboard']:
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important; color: #ffffff !important; padding: 30px; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 8px 20px rgba(79, 172, 254, 0.3);">
        <h2 style="font-weight: 700; margin-bottom: 8px;">{t['menu_dashboard'][2:]} Overview</h2>
        <p style="font-size: 16px; opacity: 0.9; margin:0;">{t['welcome']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_connection()
    df_teams_dash = pd.read_sql_query("SELECT * FROM teams", conn)
    
    total_mats = 0
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM materials"); total_mats += c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ota_materials"); total_mats += c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM oa_materials"); total_mats += c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM lift_crane_items"); total_mats += c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM generated_documents")
    total_docs = c.fetchone()[0]
    
    today = date.today()
    working_teams = 0
    resting_teams = 0
    available_teams = 0
    total_teams = len(df_teams_dash)
    
    if not df_teams_dash.empty:
        for _, row in df_teams_dash.iterrows():
            start_date_str = row.get('start_date')
            current_state = row.get('state_code') or 'S'
            is_resting = False
            is_working = False
            if start_date_str and str(start_date_str) not in ['None', 'nan', 'NaT']:
                try:
                    start_dt = datetime.strptime(str(start_date_str), "%Y-%m-%d").date()
                    if start_dt > today: is_resting = True
                    else:
                        if current_state == 'W': is_working = True
                        elif current_state == 'R': is_resting = True
                except: pass
            if is_working: working_teams += 1
            elif is_resting: resting_teams += 1
            else: available_teams += 1

    # --- TEAM LIVE STATUS ---
    st.markdown(f"<h3 style='font-weight: 600; margin-bottom: 15px;'>📡 {t['team_status']}</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card' style='border-left-color: #28a745 !important;'><div class='card-title'>{t['working_teams']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>🛠️</span>{working_teams} <span style='font-size: 18px; color: #6c757d;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card' style='border-left-color: #17a2b8 !important;'><div class='card-title'>{t['available_teams']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>✅</span>{available_teams} <span style='font-size: 18px; color: #6c757d;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card' style='border-left-color: #ffc107 !important;'><div class='card-title'>{t['resting_teams']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>🛌</span>{resting_teams} <span style='font-size: 18px; color: #6c757d;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)

    # --- GENERAL METRICS ---
    st.markdown(f"<h3 style='margin-top: 30px; font-weight: 600; margin-bottom: 15px;'>📊 General Metrics</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card' style='border-left-color: #00f2fe !important;'><div class='card-title'>{t['total_inventory']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>📦</span>{total_mats}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card' style='border-left-color: #f093fb !important;'><div class='card-title'>Files Generated</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>📝</span>{total_docs}</div></div>", unsafe_allow_html=True)
    with col3:
        c.execute("SELECT COUNT(*) FROM tasks WHERE status='Open'")
        open_tasks = c.fetchone()[0]
        if st.button(f"🚨 Open Tasks\n\n⚠️ {open_tasks}", key="open_tasks_btn", use_container_width=True):
            st.session_state.show_tasks = not st.session_state.get('show_tasks', False)

    if st.session_state.get('show_tasks', False):
        st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
        df_open_tasks = pd.read_sql_query("SELECT task_type, code_site, team_name, leader_id, created_at, notes FROM tasks WHERE status='Open' ORDER BY created_at DESC", conn)
        if not df_open_tasks.empty:
            df_open_tasks['created_at'] = pd.to_datetime(df_open_tasks['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            df_open_tasks.columns = ['Task Type', 'Code Site', 'Team Name', 'Leader ID', 'Date Opened', 'Notes']
            st.dataframe(df_open_tasks, use_container_width=True, hide_index=True)
        else:
            st.info("No open tasks right now. Great job!")
        st.markdown("</div>", unsafe_allow_html=True)

    release_connection(conn)

# ==========================================
# 2. DISPATCH & TRACKER
# ==========================================
elif main_menu == t['menu_dispatch']:
    dispatch_tool.render_tool()

# ==========================================
# 3. MATERIAL MANAGERS
# ==========================================
elif main_menu == t['menu_materials']:
    st.markdown(f"<h1 style='font-weight: 800; margin-bottom: 20px;'>{t['menu_materials'][2:]}</h1>", unsafe_allow_html=True)
    
    tab_mob, tab_ota, tab_oa, tab_lc = st.tabs([t['tab_mob'], t['tab_ota'], t['tab_oa'], t['tab_lc']])
    
    with tab_mob:
        with st.expander(t['add_new']):
            with st.form("add_mat_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1: new_part = st.text_input(t['part_number'])
                with c2: new_name = st.text_input(t['mat_name'])
                with c3: new_nature = st.selectbox(t['nature'], ["Wirless", "Power", "Trans", "Other"])
                if st.form_submit_button(t['submit'], use_container_width=True):
                    if new_name:
                        conn = get_connection(); c = conn.cursor()
                        c.execute('INSERT INTO materials (part_number, material_name, nature) VALUES (%s, %s, %s)', (new_part, new_name, new_nature))
                        conn.commit(); release_connection(conn); st.rerun()
        conn = get_connection()
        df = pd.read_sql_query("SELECT part_number, material_name, nature FROM materials", conn)
        release_connection(conn)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_ota:
        with st.expander(t['add_new']):
            with st.form("add_ota_mat_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1: new_nature = st.selectbox(t['nature'], ["Legacy", "Reusable"])
                with c2: new_desig = st.text_input(t['designation'])
                with c3: new_pn = st.text_input(t['pn'])
                if st.form_submit_button(t['submit'], use_container_width=True):
                    if new_desig:
                        conn = get_connection(); c = conn.cursor()
                        c.execute('INSERT INTO ota_materials (nature, designation, pn) VALUES (%s, %s, %s)', (new_nature, new_desig, new_pn))
                        conn.commit(); release_connection(conn); st.rerun()
        conn = get_connection()
        df = pd.read_sql_query("SELECT nature, designation, pn FROM ota_materials", conn)
        release_connection(conn)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_oa:
        st.info(t['oa_info'])
        with st.expander(t['add_new']):
            with st.form("add_oa_mat_form", clear_on_submit=True):
                new_mat = st.text_input(t['mat_name'])
                if st.form_submit_button(t['submit'], use_container_width=True):
                    if new_mat:
                        conn = get_connection(); c = conn.cursor()
                        c.execute('INSERT INTO oa_materials (material_name) VALUES (%s)', (new_mat,))
                        conn.commit(); release_connection(conn); st.rerun()
        conn = get_connection()
        df = pd.read_sql_query("SELECT material_name FROM oa_materials", conn)
        release_connection(conn)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_lc:
        with st.expander(t['add_new_item']):
            with st.form("add_lc_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1: new_code = st.text_input(t['item_code'])
                with c2: new_name = st.text_input(t['item_name'])
                with c3: new_by = st.text_input(t['item_by'])
                if st.form_submit_button(t['submit'], use_container_width=True):
                    if new_name:
                        conn = get_connection(); c = conn.cursor()
                        c.execute('INSERT INTO lift_crane_items (item_code, item_name, item_by) VALUES (%s, %s, %s)', (new_code, new_name, new_by))
                        conn.commit(); release_connection(conn); st.rerun()
        conn = get_connection()
        df = pd.read_sql_query("SELECT item_code, item_name, item_by FROM lift_crane_items", conn)
        release_connection(conn)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ==========================================
# 4. TOOLS (CASCADING DROPDOWNS)
# ==========================================
elif main_menu == t['menu_tools']:
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        selected_client = st.selectbox(t['select_client'], list(TOOL_HIERARCHY.keys()), key="client_select")
        st.session_state['selected_client'] = selected_client
    with col2:
        if selected_client:
            selected_tool_name = st.selectbox(t['select_tool'], list(TOOL_HIERARCHY[selected_client].keys()), key="tool_select")
        else:
            st.selectbox(t['select_tool'], [], key="tool_select_empty")
    
    if selected_client and selected_tool_name:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important; color: #ffffff !important; padding: 15px 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3) !important;">
            <h3 style="font-weight: 600; margin-bottom: 4px;">{selected_tool_name}</h3>
            <p style="font-size: 14px; opacity: 0.9;">{t['client_label']}: {selected_client}</p>
        </div>
        """, unsafe_allow_html=True)
        TOOL_HIERARCHY[selected_client][selected_tool_name]()