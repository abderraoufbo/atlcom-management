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
st.set_page_config(page_title="ATLCOM Management", page_icon="favicon.ico", layout="wide", initial_sidebar_state="expanded")

# --- COMPREHENSIVE TRANSLATIONS DICTIONARY ---
translations = {
    'EN': {
        'title': "ATLCOM Management", 'settings': "Settings", 'language': "Language", 'theme': "Theme",
        'main_menu': "Main Menu", 'menu_dashboard': "🏠 Dashboard", 'menu_dispatch': "📡 Dispatch & Tracker",
        'menu_materials': "📦 Material Managers", 'menu_tools': "🛠️ Tools",
        'welcome': "Welcome to your centralized project management workspace.",
        'active_clients': "Active Clients", 'total_inventory': "Total Inventory Items", 'total_teams': "Total Teams",
        'team_status': "Team Live Status", 'working_teams': "Working Teams", 'available_teams': "Available Teams", 'resting_teams': "Resting Teams",
        'select_client': "1. Select Client", 'select_tool': "2. Select Tool", 'client_label': "Client",
        'choose_db': "Choose Database:", 'tab_mob': "📦 Mobilis (ATM)", 'tab_ota': "📦 Djezzy (OTA)",
        'tab_oa': "📦 Ooredoo (OA)", 'tab_lc': "🏗️ Lift & Crane",
        'add_new': "➕ Add New Material", 'add_new_item': "➕ Add New Item", 'part_number': "Part Number",
        'mat_name': "Material Name *", 'nature': "Nature", 'submit': "Submit", 'designation': "Désignation *",
        'pn': "PN", 'oa_info': "OA list builds itself automatically in the OA Return Tool!",
        'item_code': "Item Code", 'item_name': "Item Name *", 'item_by': "Item By (Unit)",
    },
    'FR': {
        'title': "Gestion ATLCOM", 'settings': "Paramètres", 'language': "Langue", 'theme': "Thème",
        'main_menu': "Menu Principal", 'menu_dashboard': "🏠 Tableau de bord", 'menu_dispatch': "📡 Dispatch & Suivi",
        'menu_materials': "📦 Gestion du Matériel", 'menu_tools': "🛠️ Outils",
        'welcome': "Bienvenue dans votre espace de gestion de projet centralisé.",
        'active_clients': "Clients Actifs", 'total_inventory': "Total des Articles en Stock", 'total_teams': "Nombre Total d'Équipes",
        'team_status': "Statut en Direct des Équipes", 'working_teams': "Équipes en Travail", 'available_teams': "Équipes Disponibles", 'resting_teams': "Équipes en Repos",
        'select_client': "1. Sélectionner Client", 'select_tool': "2. Sélectionner Outil", 'client_label': "Client",
        'choose_db': "Choisir la Base de Données :", 'tab_mob': "📦 Mobilis (ATM)", 'tab_ota': "📦 Djezzy (OTA)",
        'tab_oa': "📦 Ooredoo (OA)", 'tab_lc': "🏗️ Levage & Grue",
        'add_new': "➕ Ajouter Nouveau Matériel", 'add_new_item': "➕ Ajouter Nouvel Article", 'part_number': "Numéro de Pièce",
        'mat_name': "Nom du Matériel *", 'nature': "Nature", 'submit': "Valider", 'designation': "Désignation *",
        'pn': "PN", 'oa_info': "La liste OA se construit automatiquement dans l'outil de retour OA !",
        'item_code': "Code Article", 'item_name': "Nom de l'Article *", 'item_by': "Unité",
    },
    'AR': {
        'title': "إدارة ATLCOM", 'settings': "الإعدادات", 'language': "اللغة", 'theme': "المظهر",
        'main_menu': "القائمة الرئيسية", 'menu_dashboard': "🏠 لوحة التحكم", 'menu_dispatch': "📡 توزيع الفرق والتتبع",
        'menu_materials': "📦 إدارة المواد", 'menu_tools': "🛠️ الأدوات",
        'welcome': "مرحباً بك في مساحة عمل إدارة المشاريع المركزية.",
        'active_clients': "العملاء النشطون", 'total_inventory': "إجمالي العناصر في المخزون", 'total_teams': "إجمالي الفرق",
        'team_status': "حالة الفرق المباشرة", 'working_teams': "الفرق العاملة", 'available_teams': "الفرق المتاحة", 'resting_teams': "الفرق في راحة",
        'select_client': "1. اختر العميل", 'select_tool': "2. اختر الأداة", 'client_label': "العميل",
        'choose_db': "اختر قاعدة البيانات:", 'tab_mob': "📦 موبيليس (ATM)", 'tab_ota': "📦 جازي (OTA)",
        'tab_oa': "📦 أوريدو (OA)", 'tab_lc': "🏗️ الرافعات والونش",
        'add_new': "➕ إضافة مادة جديدة", 'add_new_item': "➕ إضافة عنصر جديد", 'part_number': "رقم القطعة",
        'mat_name': "اسم المادة *", 'nature': "الطبيعة", 'submit': "تأكيد", 'designation': "التسمية *",
        'pn': "الرقم التعريفي (PN)", 'oa_info': "تُبنى قائمة OA تلقائياً في أداة إرجاع OA!",
        'item_code': "رمز العنصر", 'item_name': "اسم العنصر *", 'item_by': "الوحدة",
    }
}

# --- SESSION STATE INIT ---
if 'lang' not in st.session_state: st.session_state.lang = 'EN'
if 'theme' not in st.session_state: st.session_state.theme = 'Light'

t = translations[st.session_state.lang]

# --- DYNAMIC CSS (ENTERPRISE SaaS UI/UX) ---
def get_css():
    is_dark = st.session_state.theme == 'Dark'
    is_ar = st.session_state.lang == 'AR'
    
    if is_dark:
        bg_color = "#0f172a"
        sidebar_bg = "#1e293b"
        card_bg = "#1e293b"
        text_color = "#f1f5f9"
        subtext_color = "#94a3b8"
        border_color = "#334155"
        input_bg = "#0f172a"
        primary_color = "#3b82f6"
        primary_hover = "#2563eb"
    else:
        bg_color = "#f8fafc"
        sidebar_bg = "#ffffff"
        card_bg = "#ffffff"
        text_color = "#0f172a"
        subtext_color = "#64748b"
        border_color = "#e2e8f0"
        input_bg = "#f8fafc"
        primary_color = "#2563eb"
        primary_hover = "#1d4ed8"
        
    direction = "rtl" if is_ar else "ltr"
    text_align = "right" if is_ar else "left"
    
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {subtext_color}; }}

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            direction: {direction};
            text-align: {text_align};
        }}
        .stApp {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
        }}
        
        /* ==========================================
           ENTERPRISE HEADER & SIDEBAR BUTTON FIX
           ========================================== */
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        /* Hide ONLY the ugly menu/share buttons */
        #MainMenu, footer {{ visibility: hidden !important; }}
        /* FORCE the sidebar toggle button to stay visible */
        [data-testid="stSidebarCollapseButton"], button[kind="header"] {{
            display: flex !important; visibility: visible !important; opacity: 1 !important; 
            z-index: 999999 !important; position: fixed !important; top: 15px !important; right: 15px !important;
            background-color: {card_bg} !important; border: 1px solid {border_color} !important;
            color: {text_color} !important; border-radius: 8px !important; padding: 8px !important;
        }}
        
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border_color} !important;
            border-left: 1px solid {border_color} !important;
        }}
        
        /* Enterprise Sidebar Navigation */
        [data-testid="stSidebar"] div[role="radiogroup"] {{ gap: 8px; display: flex; flex-direction: column; width: 100%; }}
        [data-testid="stSidebar"] div[role="radiogroup"] > label {{
            background: transparent !important;
            border: 1px solid transparent !important;
            padding: 12px 16px !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
            display: flex !important; align-items: center !important; cursor: pointer !important;
            font-weight: 500 !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
            background-color: {input_bg} !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] [aria-checked="true"] {{
            background-color: {input_bg} !important;
            border-color: {primary_color} !important;
            box-shadow: 0 0 0 1px {primary_color} inset !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] [aria-checked="true"] > div,
        [data-testid="stSidebar"] div[role="radiogroup"] [aria-checked="true"] > div > div {{
            color: {primary_color} !important; font-weight: 600 !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {{ display: none !important; }}
        [data-testid="stSidebar"] div[role="radiogroup"] > label > div:last-child {{ width: 100% !important; }}
        
        /* Typography & Layout */
        .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{ color: {text_color} !important; }}
        .stRadio > div > label, .stSelectbox > div > div > div {{ color: {text_color} !important; }}
        .block-container {{ padding-top: 3rem; padding-bottom: 3rem; max-width: 1200px; margin: 0 auto; }}
        
        /* Enterprise Buttons */
        .stButton > button, .stFormSubmitButton > button {{
            color: #ffffff !important;
            background-color: {primary_color} !important;
            border: none !important; border-radius: 8px !important; font-weight: 600 !important;
            transition: all 0.2s ease !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            padding: 10px 20px !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            background-color: {primary_hover} !important;
            border: none !important;
        }}
        
        /* Enterprise Cards (Clean, Solid, Subtle Shadow) */
        div.card {{
            background-color: {card_bg} !important;
            padding: 24px !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03) !important;
            border: 1px solid {border_color} !important;
            margin-bottom: 16px !important;
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        }}
        div.card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03) !important;
        }}
        .card-title {{ font-size: 14px; color: {subtext_color}; font-weight: 500; margin-bottom: 8px; }}
        .card-value {{ font-size: 28px; font-weight: 700; color: {text_color}; }}
        
        /* Open Tasks Button styled as Enterprise Card */
        button[k="open_tasks_btn"] {{
            background-color: {card_bg} !important;
            border: 1px solid {border_color} !important;
            border-left: 4px solid #ef4444 !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
            color: {text_color} !important;
            height: 100% !important; min-height: 110px !important;
            display: flex !important; flex-direction: column !important; justify-content: center !important;
            align-items: flex-start !important; text-align: left !important;
            font-weight: 600 !important; transition: all 0.2s ease !important; margin-bottom: 16px !important;
        }}
        button[k="open_tasks_btn"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
            background-color: {card_bg} !important;
        }}
        
        .hero-banner {{ background-color: {primary_color} !important; color: #ffffff !important; padding: 32px; border-radius: 12px; margin-bottom: 24px; }}
        .hero-banner h2, .hero-banner p {{ color: #ffffff !important; margin: 0; }}
        .tool-banner {{ background-color: {primary_color} !important; color: #ffffff !important; padding: 20px 24px; border-radius: 10px; margin-bottom: 20px; }}
        .tool-banner h3, .tool-banner p {{ color: #ffffff !important; }}
        
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background-color: transparent !important; padding: 0 !important; border-bottom: 1px solid {border_color}; border-radius: 0 !important; }}
        .stTabs [data-baseweb="tab"] {{ background-color: transparent !important; border-radius: 0 !important; color: {subtext_color} !important; border: none !important; border-bottom: 2px solid transparent !important; font-weight: 500 !important; padding: 12px 16px !important; }}
        .stTabs [aria-selected="true"] {{ background-color: transparent !important; color: {primary_color} !important; border-bottom: 2px solid {primary_color} !important; }}
        
        /* Enterprise Inputs (High Contrast Text) */
        .stTextInput > div > div, .stSelectbox > div > div > div {{
            background-color: {input_bg} !important; border: 1px solid {border_color} !important; border-radius: 8px; color: {text_color} !important;
        }}
        .stTextInput > div > div input {{ color: {text_color} !important; }}
        .stTextInput > div > div input::placeholder {{ color: {subtext_color} !important; opacity: 1 !important; }}
        .stTextInput > div > div:focus-within, .stSelectbox > div > div > div:focus-within {{
            border-color: {primary_color} !important; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
        }}
        
        .stDataFrame {{ background-color: {card_bg} !important; border: 1px solid {border_color} !important; border-radius: 8px !important; padding: 0 !important; overflow: hidden; }}
        div[data-testid="stDataFrame"] div, div[data-testid="stTable"] div {{ color: {text_color} !important; }}
        
        /* ==========================================
           ENTERPRISE LOGIN PAGE
           ========================================== */
        .login-container {{ display: flex; justify-content: center; align-items: center; min-height: calc(100vh - 60px); padding: 20px; }}
        .login-card {{ 
            background-color: {card_bg} !important;
            padding: 40px !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05), 0 8px 10px -6px rgba(0,0,0,0.01), 0 0 0 1px {border_color} inset !important;
            border: none !important;
            width: 100% !important; max-width: 400px !important;
            text-align: center !important;
            display: flex !important; flex-direction: column !important; align-items: center !important;
        }}
        .login-icon-wrapper {{
            width: 60px; height: 60px; background-color: {primary_color};
            border-radius: 12px; margin: 0 auto 20px auto; display: flex; align-items: center; justify-content: center;
            color: white; font-size: 28px;
        }}
        
        .login-card [data-testid="stRadio"] > div {{ flex-direction: row !important; display: flex !important; gap: 8px !important; background: {input_bg} !important; padding: 4px !important; border-radius: 8px !important; width: 100% !important; border: 1px solid {border_color} !important; }}
        .login-card [data-testid="stRadio"] > div > label {{
            background: transparent !important; border: none !important; padding: 10px !important;
            border-radius: 6px !important; flex: 1 !important; text-align: center !important; cursor: pointer !important;
            transition: all 0.2s ease !important; font-size: 14px !important; font-weight: 500 !important; color: {subtext_color} !important;
        }}
        .login-card [data-testid="stRadio"] > div > label:hover {{ background: transparent !important; color: {text_color} !important; }}
        .login-card [data-testid="stRadio"] > div > label[data-checked="true"] {{
            background-color: {card_bg} !important; color: {primary_color} !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }}
        .login-card [data-testid="stRadio"] > div > label > div:first-child {{ display: none !important; }}
        .login-card [data-testid="stRadio"] > div > label > div:last-child {{ width: 100% !important; font-size: 14px !important; font-weight: 600 !important; }}
        
        .login-card .stTextInput > div > div {{
            background-color: {input_bg} !important; border: 1px solid {border_color} !important; border-radius: 8px !important; padding: 8px 12px !important;
        }}
        .login-card .stButton {{ width: 100%; display: flex; justify-content: center; margin-top: 8px; }}
        .login-card .stButton > button {{
            background-color: {primary_color} !important; border: none !important; padding: 12px 0 !important; border-radius: 8px !important;
            font-size: 15px !important; font-weight: 600 !important; box-shadow: none !important;
        }}
        
        @media only screen and (max-width: 768px) {{
            .block-container {{ padding-top: 4rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100% !important; }}
            [data-testid="stHorizontalBlock"] {{ flex-direction: column !important; width: 100% !important; align-items: center !important; gap: 10px !important; }}
            [data-testid="stHorizontalBlock"] > div {{ width: 100% !important; }}
            .login-card [data-testid="stRadio"] > div {{ flex-direction: column !important; background: transparent !important; border: none !important; padding: 0 !important; gap: 12px !important; }}
            .login-card [data-testid="stRadio"] > div > label {{ background-color: {input_bg} !important; border: 1px solid {border_color} !important; }}
        }}
    </style>
    """

st.markdown(get_css(), unsafe_allow_html=True)

init_db()

# Force sidebar to exist so the toggle button shows up on the login screen
st.sidebar.markdown("")

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
    # --- ENTERPRISE LOGIN PAGE ---
    st.markdown("<div class='login-container'><div class='login-card'>", unsafe_allow_html=True)
    st.markdown("<div class='login-icon-wrapper'>🛠️</div>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-weight: 800; margin-bottom: 5px;'>ATLCOM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity: 0.7; margin-bottom: 24px; font-size: 14px;'>Management Portal</p>", unsafe_allow_html=True)
    
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
            
    st.markdown("</div></div>", unsafe_allow_html=True)
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

# --- SIDEBAR ---
st.sidebar.markdown(f"<h1 style='font-size: 20px; font-weight: 700; color: {('#3b82f6' if st.session_state.theme == 'Dark' else '#2563eb')}; margin-bottom: 0; letter-spacing: -0.5px;'>ATLCOM</h1>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='font-size: 12px; color: #64748b; margin-top: 0;'>Management Portal</p>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 16px 0;'>", unsafe_allow_html=True)

with st.sidebar.expander(f"⚙️ {t['settings']}"):
    col_lang, col_theme = st.columns(2)
    with col_lang:
        lang = st.selectbox(f"{t['language']}", ['EN', 'FR', 'AR'], key='lang_select')
        if lang != st.session_state.lang:
            st.session_state.lang = lang
            st.rerun()
    with col_theme:
        theme = st.selectbox(f"{t['theme']}", ['Light', 'Dark'], key='theme_select')
        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.rerun()

st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 16px 0;'>", unsafe_allow_html=True)

# Manager Logout Button
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

t = translations[st.session_state.lang]
main_menu = st.sidebar.radio(f"{t['main_menu']}", [t['menu_dashboard'], t['menu_dispatch'], t['menu_materials'], t['menu_tools']])

# ==========================================
# 1. DASHBOARD
# ==========================================
if main_menu == t['menu_dashboard']:
    st.markdown(f"""
    <div class="hero-banner">
        <h2 style="font-weight: 700; margin-bottom: 8px;">{t['menu_dashboard'][2:]} Overview</h2>
        <p style="font-size: 15px; opacity: 0.9;">{t['welcome']}</p>
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
    st.markdown(f"<h3 style='font-weight: 600; margin-bottom: 16px; font-size: 18px;'>📡 {t['team_status']}</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card' style='border-left: 4px solid #10b981 !important;'><div class='card-title'>{t['working_teams']}</div><div class='card-value'><span style='margin-right: 8px;'>🛠️</span>{working_teams} <span style='font-size: 16px; color: #94a3b8; font-weight: 500;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card' style='border-left: 4px solid #3b82f6 !important;'><div class='card-title'>{t['available_teams']}</div><div class='card-value'><span style='margin-right: 8px;'>✅</span>{available_teams} <span style='font-size: 16px; color: #94a3b8; font-weight: 500;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card' style='border-left: 4px solid #f59e0b !important;'><div class='card-title'>{t['resting_teams']}</div><div class='card-value'><span style='margin-right: 8px;'>🛌</span>{resting_teams} <span style='font-size: 16px; color: #94a3b8; font-weight: 500;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)

    # --- GENERAL METRICS ---
    st.markdown(f"<h3 style='margin-top: 32px; font-weight: 600; margin-bottom: 16px; font-size: 18px;'>📊 General Metrics</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card' style='border-left: 4px solid #6366f1 !important;'><div class='card-title'>{t['total_inventory']}</div><div class='card-value'><span style='margin-right: 8px;'>📦</span>{total_mats}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card' style='border-left: 4px solid #8b5cf6 !important;'><div class='card-title'>Files Generated</div><div class='card-value'><span style='margin-right: 8px;'>📝</span>{total_docs}</div></div>", unsafe_allow_html=True)
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
# 3. MATERIAL MANAGERS (TABS UI)
# ==========================================
elif main_menu == t['menu_materials']:
    st.markdown(f"<h1 style='font-weight: 700; font-size: 24px; margin-bottom: 20px;'>{t['menu_materials'][2:]}</h1>", unsafe_allow_html=True)
    
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
    st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 16px 0;'>", unsafe_allow_html=True)
    
    clients = list(TOOL_HIERARCHY.keys())
    selected_client = st.sidebar.selectbox(t['select_client'], clients, key="client_select")
    st.session_state['selected_client'] = selected_client
    
    if selected_client:
        tools = list(TOOL_HIERARCHY[selected_client].keys())
        selected_tool_name = st.sidebar.selectbox(t['select_tool'], tools, key="tool_select")
        
        st.markdown(f"""
        <div class="tool-banner">
            <h3 style="font-weight: 600; margin-bottom: 4px;">{selected_tool_name}</h3>
            <p style="font-size: 14px; opacity: 0.9;">{t['client_label']}: {selected_client}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if selected_tool_name:
            TOOL_HIERARCHY[selected_client][selected_tool_name]()