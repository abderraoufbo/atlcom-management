import streamlit as st
import sys
import os
import sqlite3
import pandas as pd
from datetime import date, datetime
from tools import leader_portal
from database import init_db, get_connection, release_connection

sys.path.append(os.path.abspath("core"))
from database import init_db, get_connection

# Import your tools
from tools import mobilis_rn_tool
from tools import ota_odr_tool
from tools import oa_return_tool
from tools import lift_crane_tool
from tools import dispatch_tool

# --- PAGE CONFIG ---
st.set_page_config(page_title="ATLCOM Management", page_icon="🛠️", layout="wide", initial_sidebar_state="expanded")

# --- COMPREHENSIVE TRANSLATIONS DICTIONARY ---
translations = {
    'EN': {
        'title': "ATLCOM Management",
        'settings': "Settings",
        'language': "Language",
        'theme': "Theme",
        'main_menu': "Main Menu",
        'menu_dashboard': "🏠 Dashboard",
        'menu_dispatch': "📡 Dispatch & Tracker",
        'menu_materials': "📦 Material Managers",
        'menu_tools': "🛠️ Tools",
        'welcome': "Welcome to your centralized project management workspace.",
        'active_clients': "Active Clients",
        'total_inventory': "Total Inventory Items",
        'total_teams': "Total Teams",
        'team_status': "Team Live Status",
        'working_teams': "Working Teams",
        'available_teams': "Available Teams",
        'resting_teams': "Resting Teams",
        'select_client': "1. Select Client",
        'select_tool': "2. Select Tool",
        'client_label': "Client",
        'choose_db': "Choose Database:",
        'tab_mob': "📦 Mobilis (ATM)",
        'tab_ota': "📦 Djezzy (OTA)",
        'tab_oa': "📦 Ooredoo (OA)",
        'tab_lc': "🏗️ Lift & Crane",
        'add_new': "➕ Add New Material",
        'add_new_item': "➕ Add New Item",
        'part_number': "Part Number",
        'mat_name': "Material Name *",
        'nature': "Nature",
        'submit': "Submit",
        'designation': "Désignation *",
        'pn': "PN",
        'oa_info': "OA list builds itself automatically in the OA Return Tool!",
        'item_code': "Item Code",
        'item_name': "Item Name *",
        'item_by': "Item By (Unit)",
    },
    'FR': {
        'title': "Gestion ATLCOM",
        'settings': "Paramètres",
        'language': "Langue",
        'theme': "Thème",
        'main_menu': "Menu Principal",
        'menu_dashboard': "🏠 Tableau de bord",
        'menu_dispatch': "📡 Dispatch & Suivi",
        'menu_materials': "📦 Gestion du Matériel",
        'menu_tools': "🛠️ Outils",
        'welcome': "Bienvenue dans votre espace de gestion de projet centralisé.",
        'active_clients': "Clients Actifs",
        'total_inventory': "Total des Articles en Stock",
        'total_teams': "Nombre Total d'Équipes",
        'team_status': "Statut en Direct des Équipes",
        'working_teams': "Équipes en Travail",
        'available_teams': "Équipes Disponibles",
        'resting_teams': "Équipes en Repos",
        'select_client': "1. Sélectionner Client",
        'select_tool': "2. Sélectionner Outil",
        'client_label': "Client",
        'choose_db': "Choisir la Base de Données :",
        'tab_mob': "📦 Mobilis (ATM)",
        'tab_ota': "📦 Djezzy (OTA)",
        'tab_oa': "📦 Ooredoo (OA)",
        'tab_lc': "🏗️ Levage & Grue",
        'add_new': "➕ Ajouter Nouveau Matériel",
        'add_new_item': "➕ Ajouter Nouvel Article",
        'part_number': "Numéro de Pièce",
        'mat_name': "Nom du Matériel *",
        'nature': "Nature",
        'submit': "Valider",
        'designation': "Désignation *",
        'pn': "PN",
        'oa_info': "La liste OA se construit automatiquement dans l'outil de retour OA !",
        'item_code': "Code Article",
        'item_name': "Nom de l'Article *",
        'item_by': "Unité",
    },
    'AR': {
        'title': "إدارة ATLCOM",
        'settings': "الإعدادات",
        'language': "اللغة",
        'theme': "المظهر",
        'main_menu': "القائمة الرئيسية",
        'menu_dashboard': "🏠 لوحة التحكم",
        'menu_dispatch': "📡 توزيع الفرق والتتبع",
        'menu_materials': "📦 إدارة المواد",
        'menu_tools': "🛠️ الأدوات",
        'welcome': "مرحباً بك في مساحة عمل إدارة المشاريع المركزية.",
        'active_clients': "العملاء النشطون",
        'total_inventory': "إجمالي العناصر في المخزون",
        'total_teams': "إجمالي الفرق",
        'team_status': "حالة الفرق المباشرة",
        'working_teams': "الفرق العاملة",
        'available_teams': "الفرق المتاحة",
        'resting_teams': "الفرق في راحة",
        'select_client': "1. اختر العميل",
        'select_tool': "2. اختر الأداة",
        'client_label': "العميل",
        'choose_db': "اختر قاعدة البيانات:",
        'tab_mob': "📦 موبيليس (ATM)",
        'tab_ota': "📦 جازي (OTA)",
        'tab_oa': "📦 أوريدو (OA)",
        'tab_lc': "🏗️ الرافعات والونش",
        'add_new': "➕ إضافة مادة جديدة",
        'add_new_item': "➕ إضافة عنصر جديد",
        'part_number': "رقم القطعة",
        'mat_name': "اسم المادة *",
        'nature': "الطبيعة",
        'submit': "تأكيد",
        'designation': "التسمية *",
        'pn': "الرقم التعريفي (PN)",
        'oa_info': "تُبنى قائمة OA تلقائياً في أداة إرجاع OA!",
        'item_code': "رمز العنصر",
        'item_name': "اسم العنصر *",
        'item_by': "الوحدة",
    }
}

# --- SESSION STATE INIT ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'EN'
if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark'

t = translations[st.session_state.lang]

# --- DYNAMIC CSS (PREMIUM UI/UX & GLASSMORPHISM) ---
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
    else:
        body_bg = "linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)"
        glass_bg = "rgba(255, 255, 255, 0.65)"
        glass_border = "rgba(255, 255, 255, 0.9)"
        text_color = "#1e293b"
        card_title_color = "#64748b"
        input_bg = "rgba(255, 255, 255, 0.5)"
        df_bg = "rgba(255, 255, 255, 0.8)"
        
    direction = "rtl" if is_ar else "ltr"
    text_align = "right" if is_ar else "left"
    
    return f"""
    <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #0078D7; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #0056b3; }}

        html, body, [class*="css"] {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            direction: {direction};
            text-align: {text_align};
        }}
        
        /* Animated Gradient Background for App */
        .stApp {{
            background: {body_bg} !important;
            color: {text_color} !important;
        }}
        
        /* Make Header Transparent to keep sidebar button */
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        
        /* Glassmorphism Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {glass_bg} !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-left: 1px solid {glass_border} !important;
            border-right: 1px solid {glass_border} !important;
        }}
        
        /* ==========================================
           SIDEBAR RADIO BUTTONS -> GLASS BUTTONS
           ========================================== */
        [data-testid="stSidebar"] div[role="radiogroup"] {{
            gap: 12px;
            display: flex;
            flex-direction: column;
            width: 100%;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] > label {{
            background: {input_bg} !important;
            backdrop-filter: blur(4px) !important;
            border: 1px solid {glass_border} !important;
            padding: 15px !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
            cursor: pointer !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
            background: {glass_bg} !important;
            transform: translateX(5px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] [aria-checked="true"] {{
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
            border-color: transparent !important;
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4) !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] [aria-checked="true"] > div {{
            color: #ffffff !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] [aria-checked="true"] > div > div {{
            color: #ffffff !important; 
        }}
        /* Hide the ugly radio circle */
        [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {{
            display: none !important;
        }}
        /* Fix text container width */
        [data-testid="stSidebar"] div[role="radiogroup"] > label > div:last-child {{
            width: 100% !important;
        }}
        
        /* Hardened Text Colors */
        .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
            color: {text_color} !important;
        }}
        .stRadio > div > label, .stSelectbox > div > div > div {{
            color: {text_color} !important;
        }}
        
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        /* FIX: BUTTON CONTRAST & STYLING */
        .stButton > button, .stFormSubmitButton > button {{
            color: #ffffff !important;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 6px rgba(79, 172, 254, 0.2) !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(79, 172, 254, 0.4) !important;
            background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%) !important;
        }}
        
        /* Glassmorphism Cards with Glowing Accent */
        div.card {{
            background-color: {glass_bg} !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid {glass_border} !important;
            margin-bottom: 15px;
            border-left: 4px solid #4facfe !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        div.card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(79, 172, 254, 0.2) !important;
        }}
        .card-title {{ font-size: 14px; color: {card_title_color}; font-weight: 500; margin-bottom: 5px; }}
        .card-value {{ font-size: 32px; font-weight: 800; color: {text_color}; }}
        
        /* Dashboard Hero Banner */
        .hero-banner {{
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
            color: #ffffff !important;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 25px;
            box-shadow: 0 8px 20px rgba(79, 172, 254, 0.3);
        }}
        .hero-banner h2, .hero-banner p {{ color: #ffffff !important; margin: 0; }}
        
        /* Tool Banner */
        .tool-banner {{
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
            color: #ffffff !important; 
            padding: 15px 25px; 
            border-radius: 12px; 
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3) !important;
        }}
        .tool-banner h3, .tool-banner p {{ color: #ffffff !important; }}
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {{ 
            gap: 10px; 
            background-color: transparent !important; 
            padding: 10px 10px 0 10px; 
            border-radius: 8px 8px 0 0; 
        }}
        .stTabs [data-baseweb="tab"] {{ 
            background-color: {input_bg} !important; 
            backdrop-filter: blur(4px) !important;
            border-radius: 8px 8px 0 0; 
            color: {text_color} !important; 
            border: 1px solid {glass_border} !important;
        }}
        .stTabs [aria-selected="true"] {{ 
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important; 
            color: #ffffff !important; 
        }}
        
        /* Inputs & Dataframes */
        .stTextInput > div > div, .stSelectbox > div > div > div {{
            background-color: {input_bg} !important; 
            backdrop-filter: blur(4px) !important;
            border: 1px solid {glass_border} !important; 
            border-radius: 8px; 
            color: {text_color} !important;
        }}
        .stDataFrame {{
            background-color: {df_bg} !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid {glass_border} !important;
            border-radius: 12px !important;
            padding: 10px !important;
        }}
        div[data-testid="stDataFrame"] div, div[data-testid="stTable"] div {{
            color: {text_color} !important;
        }}
        
        /* ==========================================
           SUPERCHARGED MOBILE RESPONSIVENESS
           ========================================== */
        @media only screen and (max-width: 768px) {{
            /* Push content down so it doesn't overlap the sidebar toggle button */
            .block-container {{
                padding-top: 4rem !important; 
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                max-width: 100% !important;
            }}
            
            [data-testid="stHorizontalBlock"] {{
                flex-direction: column !important;
                width: 100% !important;
                align-items: center !important;
                gap: 10px !important;
            }}
            
            [data-testid="stHorizontalBlock"] > div {{
                width: 100% !important;
            }}
            
            div.card {{
                padding: 15px;
                margin-left: auto !important;
                margin-right: auto !important;
                width: 100% !important;
                box-sizing: border-box !important;
                border-left: none !important;
                border-top: 4px solid #4facfe !important;
            }}
            .card-value {{ font-size: 26px; }}
            .card-title {{ font-size: 12px; }}
            
            .hero-banner, .tool-banner {{
                padding: 15px;
                border-radius: 12px;
            }}
            .hero-banner h2 {{ font-size: 20px; }}
            .tool-banner h3 {{ font-size: 18px; margin-bottom: 5px; }}
            
            iframe, .stDataFrame {{
                width: 100% !important;
                max-width: 100% !important;
            }}
            
            .stTabs [data-baseweb="tab-list"] {{
                gap: 5px;
                padding: 5px;
                overflow-x: auto;
            }}
            .stTabs [data-baseweb="tab"] {{
                padding: 8px 12px;
                font-size: 14px;
                white-space: nowrap;
            }}
        }}
    </style>
    """

st.markdown(get_css(), unsafe_allow_html=True)

init_db()

# --- ROUTING: Check if Team Leader is accessing the portal ---
query_params = st.query_params
if 'portal' in query_params and query_params['portal'] == 'leader':
    leader_portal.render_portal()
    st.stop() # Stop executing the rest of the GM app

# --- TOOL HIERARCHY CONFIGURATION ---
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
st.sidebar.markdown(f"<h1 style='font-size: 24px; font-weight: 800; color: #0078D7; margin-bottom: 0;'>🛠️ {t['title']}</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size: 12px; color: #6c757d; margin-top: 0;'>Modular Architecture v2.0</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

with st.sidebar.expander(f"⚙️ {t['settings']}"):
    col_lang, col_theme = st.columns(2)
    with col_lang:
        lang = st.selectbox(f"{t['language']}", ['EN', 'FR', 'AR'], key='lang_select')
        if lang != st.session_state.lang:
            st.session_state.lang = lang
            st.rerun()
    with col_theme:
        # Using on_change to handle the theme switch more smoothly
        current_theme_index = 0 if st.session_state.theme == 'Light' else 1
        new_theme = st.selectbox(f"{t['theme']}", ['Light', 'Dark'], index=current_theme_index, key='theme_select')
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

st.sidebar.markdown("---")

t = translations[st.session_state.lang]

# The CSS transforms this radio into beautiful glass buttons
main_menu = st.sidebar.radio(f"{t['main_menu']}", [t['menu_dashboard'], t['menu_dispatch'], t['menu_materials'], t['menu_tools']])

# ==========================================
# 1. DASHBOARD (STUNNING UI)
# ==========================================
if main_menu == t['menu_dashboard']:
    # Hero Banner
    st.markdown(f"""
    <div class="hero-banner">
        <h2>{t['menu_dashboard'][2:]} Overview</h2>
        <p style="font-size: 16px; margin-top: 5px;">{t['welcome']}</p>
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
    release_connection(conn)
    
    # --- SMART STATUS CALCULATION FOR DASHBOARD ---
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
                    if start_dt > today:
                        is_resting = True # Future date means they are resting
                    else:
                        if current_state == 'W':
                            is_working = True
                        elif current_state == 'R':
                            is_resting = True
                except:
                    pass
            
            if is_working:
                working_teams += 1
            elif is_resting:
                resting_teams += 1
            else:
                available_teams += 1
                
    # --- TEAM LIVE STATUS (1ST) ---
    st.markdown(f"<h3 style='font-weight: 600; margin-bottom: 15px;'>📡 {t['team_status']}</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card' style='border-left-color: #28a745 !important;'><div class='card-title'>{t['working_teams']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>🛠️</span>{working_teams} <span style='font-size: 18px; color: #6c757d;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card' style='border-left-color: #17a2b8 !important;'><div class='card-title'>{t['available_teams']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>✅</span>{available_teams} <span style='font-size: 18px; color: #6c757d;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card' style='border-left-color: #ffc107 !important;'><div class='card-title'>{t['resting_teams']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>🛌</span>{resting_teams} <span style='font-size: 18px; color: #6c757d;'>/ {total_teams}</span></div></div>", unsafe_allow_html=True)

    # --- GENERAL METRICS (2ND) ---
    st.markdown(f"<h3 style='margin-top: 30px; font-weight: 600; margin-bottom: 15px;'>📊 General Metrics</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card'><div class='card-title'>{t['active_clients']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>🏢</span>3</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card' style='border-left-color: #00f2fe !important;'><div class='card-title'>{t['total_inventory']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>📦</span>{total_mats}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card' style='border-left-color: #f093fb !important;'><div class='card-title'>{t['total_teams']}</div><div class='card-value'><span style='font-size: 28px; margin-right: 10px;'>👥</span>{total_teams}</div></div>", unsafe_allow_html=True)

# ==========================================
# 2. DISPATCH & TRACKER
# ==========================================
elif main_menu == t['menu_dispatch']:
    dispatch_tool.render_tool()

# ==========================================
# 3. MATERIAL MANAGERS (TABS UI)
# ==========================================
elif main_menu == t['menu_materials']:
    st.markdown(f"<h1 style='font-weight: 800;'>{t['menu_materials'][2:]}</h1>", unsafe_allow_html=True)
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) # Spacer
    
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
                        c.execute('INSERT INTO materials (part_number, material_name, nature) VALUES (?, ?, ?)', (new_part, new_name, new_nature))
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
                        c.execute('INSERT INTO ota_materials (nature, designation, pn) VALUES (?, ?, ?)', (new_nature, new_desig, new_pn))
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
                        c.execute('INSERT INTO oa_materials (material_name) VALUES (?)', (new_mat,))
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
                        c.execute('INSERT INTO lift_crane_items (item_code, item_name, item_by) VALUES (?, ?, ?)', (new_code, new_name, new_by))
                        conn.commit(); release_connection(conn); st.rerun()
        conn = get_connection()
        df = pd.read_sql_query("SELECT item_code, item_name, item_by FROM lift_crane_items", conn)
        release_connection(conn)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ==========================================
# 4. TOOLS (CASCADING DROPDOWNS)
# ==========================================
elif main_menu == t['menu_tools']:
    st.sidebar.markdown("---")
    
    clients = list(TOOL_HIERARCHY.keys())
    selected_client = st.sidebar.selectbox(t['select_client'], clients, key="client_select")
    st.session_state['selected_client'] = selected_client
    
    if selected_client:
        tools = list(TOOL_HIERARCHY[selected_client].keys())
        selected_tool_name = st.sidebar.selectbox(t['select_tool'], tools, key="tool_select")
        
        st.markdown(f"""
        <div class="tool-banner">
            <h3>{selected_tool_name}</h3>
            <p>{t['client_label']}: {selected_client}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if selected_tool_name:
            TOOL_HIERARCHY[selected_client][selected_tool_name]()