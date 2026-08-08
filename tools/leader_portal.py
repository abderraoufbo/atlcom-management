import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
from datetime import date, datetime
import sys, os
from database import get_connection, release_connection

sys.path.append(os.path.abspath("core"))
from database import get_connection
from tools.dispatch_tool import ALGERIAN_WILAYAS, DEFAULT_LAT, DEFAULT_LON

# --- TRANSLATIONS FOR PORTAL ---
portal_translations = {
    'EN': {
        'title': "📡 Team Leader Portal",
        'language': "Language",
        'login': "Login",
        'enter_id': "Enter your Team Leader ID",
        'invalid': "Invalid Leader ID. Please check with your manager.",
        'welcome': "Welcome,",
        'current_status': "Current Status",
        'location': "Location",
        'update_status': "Update Your Status",
        'new_state': "New State",
        'site_id': "Site ID / Current Location Name *",
        'select_wilaya': "Select Wilaya (For Map Pin)",
        'return_date': "Planned Return to Work Date",
        'notes': "Notes (Optional)",
        'update_btn': "🚀 Update Status",
        'error_site': "Please enter the Site ID.",
        'success': "Status updated successfully! The General Manager has been notified.",
        'logout': "Logout",
        'get_gps': "📍 Get My Exact GPS",
        'gps_locked': "Exact GPS Locked!",
        'states': {"W": "🟢 Working", "R": "🟠 Resting", "S": "🔵 Stand-by", "T": "🔴 On Road", "P": "🔴 Urgency"}
    },
    'FR': {
        'title': "📡 Portail du Chef d'Équipe",
        'language': "Langue",
        'login': "Connexion",
        'enter_id': "Entrez votre ID de Chef d'Équipe",
        'invalid': "ID invalide. Veuillez vérifier auprès de votre responsable.",
        'welcome': "Bienvenue,",
        'current_status': "Statut Actuel",
        'location': "Emplacement",
        'update_status': "Mettre à jour votre statut",
        'new_state': "Nouvel État",
        'site_id': "ID du Site / Emplacement Actuel *",
        'select_wilaya': "Sélectionner la Wilaya (Pour la Carte)",
        'return_date': "Date de Retour Prévue",
        'notes': "Notes (Optionnel)",
        'update_btn': "🚀 Mettre à jour",
        'error_site': "Veuillez entrer l'ID du site.",
        'success': "Statut mis à jour avec succès ! Le directeur a été notifié.",
        'logout': "Déconnexion",
        'get_gps': "📍 Obtenir mon GPS exact",
        'gps_locked': "GPS exact verrouillé !",
        'states': {"W": "🟢 En Travail", "R": "🟠 En Repos", "S": "🔵 Disponible", "T": "🔴 En Route", "P": "🔴 Urgence"}
    },
    'AR': {
        'title': "📡 بوابة قادة الفرق",
        'language': "اللغة",
        'login': "تسجيل الدخول",
        'enter_id': "أدخل معرف قائد الفريق",
        'invalid': "معرف غير صالح. يرجى التحقق من مديرك.",
        'welcome': "مرحباً،",
        'current_status': "الحالة الحالية",
        'location': "الموقع",
        'update_status': "تحديث حالتك",
        'new_state': "الحالة الجديدة",
        'site_id': "رقم الموقع / اسم الموقع الحالي *",
        'select_wilaya': "اختر الولاية (لخريطة الموقع)",
        'return_date': "تاريخ العودة المتوقع للعمل",
        'notes': "ملاحظات (اختياري)",
        'update_btn': "🚀 تحديث الحالة",
        'error_site': "الرجاء إدخال رقم الموقع.",
        'success': "تم تحديث الحالة بنجاح! تم إبلاغ المدير العام.",
        'logout': "تسجيل الخروج",
        'get_gps': "📍 احصل على موقعي الدقيق",
        'gps_locked': "تم تحديد الموقع الدقيق!",
        'states': {"W": "🟢 يعمل", "R": "🟠 في راحة", "S": "🔵 مستعد", "T": "🔴 على الطريق", "P": "🔴 طارئ"}
    }
}

def render_portal():
    if 'portal_lang' not in st.session_state:
        st.session_state.portal_lang = 'EN'
    
    t = portal_translations[st.session_state.portal_lang]
    is_ar = st.session_state.portal_lang == 'AR'
    direction = "rtl" if is_ar else "ltr"
    text_align = "right" if is_ar else "left"
    
    st.markdown(f"""
    <style>
        section[data-testid="stSidebar"] {{ display: none !important; }}
        .block-container {{ max-width: 600px !important; margin: 0 auto !important; padding-top: 2rem !important; direction: {direction}; text-align: {text_align}; }}
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        lang_select = st.selectbox(f"🌍 {t['language']}", ['EN', 'FR', 'AR'], key='lang_select_portal', label_visibility="collapsed")
        if lang_select != st.session_state.portal_lang:
            st.session_state.portal_lang = lang_select
            st.rerun()
            
    st.title(t['title'])
    
    query_params = st.query_params
    if 'lid' in query_params and not st.session_state.get('leader_logged_in'):
        leader_id = query_params['lid']
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=%(lid)s", conn, params={"lid": leader_id})
        release_connection(conn)
        if not df.empty:
            st.session_state.leader_logged_in = True
            st.session_state.leader_data = df.iloc[0].to_dict()

    if 'leader_logged_in' not in st.session_state:
        st.session_state.leader_logged_in = False
        
    if not st.session_state.leader_logged_in:
        st.subheader(t['login'])
        leader_id = st.text_input(t['enter_id'])
        if st.button(t['login'], type="primary", use_container_width=True):
            conn = get_connection()
            df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=?", conn, params=(leader_id,))
            release_connection(conn)
            if not df.empty:
                st.query_params['lid'] = leader_id
                st.session_state.leader_logged_in = True
                st.session_state.leader_data = df.iloc[0].to_dict()
                st.rerun()
            else:
                st.error(t['invalid'])
        return

    team = st.session_state.leader_data
    st.success(f"{t['welcome']} {team['leader_name']} ({team['team_name']})")
    
    current_state = team.get('state_code') or 'S'
    st.info(f"{t['current_status']}: **{t['states'].get(current_state, 'Unknown')}**\n\n{t['location']}: **{team.get('current_location_name') or 'N/A'}**")
    
    st.divider()
    st.subheader(t['update_status'])
    
    state_options = ["W", "R", "S", "T", "P"]
    state_labels = [f"{s} - {t['states'][s]}" for s in state_options]
    selected_idx = st.selectbox(t['new_state'], range(len(state_labels)), format_func=lambda x: state_labels[x])
    new_state_code = state_options[selected_idx]
    
    new_loc = ""
    return_date = None
    update_lat, update_lon = None, None
    
    if new_state_code == "W":
        new_loc = st.text_input(t['site_id'], value=team.get('current_location_name') or "")
        new_wilaya = st.selectbox(t['select_wilaya'], list(ALGERIAN_WILAYAS.keys()), index=list(ALGERIAN_WILAYAS.keys()).index(team.get('wilaya')) if team.get('wilaya') in ALGERIAN_WILAYAS else 0)
        
        # Default to Wilaya center
        update_lat, update_lon = ALGERIAN_WILAYAS[new_wilaya]
        
        # --- EXACT GPS TRACKING BUTTON ---
        st.markdown("##### 📍 Exact Location (Optional)")
        # HTML/JS to grab GPS from the phone
        components.html(f"""
        <button onclick="getLocation()" style="width:100%; padding:12px; border-radius:8px; border:none; background:linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); color:white; font-weight:600; cursor:pointer;">{t['get_gps']}</button>
        <p id="gps-status" style="text-align:center; margin-top:10px; font-weight:bold;"></p>
        <script>
        function getLocation() {{
            const status = document.getElementById('gps-status');
            status.innerText = "Locating...";
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(showPosition, showError);
            }} else {{
                status.innerText = "Geolocation is not supported by this browser.";
            }}
        }}
        function showPosition(position) {{
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const status = document.getElementById('gps-status');
            status.innerText = "{t['gps_locked']}";
            status.style.color = "green";
            
            // Send data back to Streamlit by updating URL params
            const url = new URL(window.parent.location.href);
            url.searchParams.set('gps_lat', lat);
            url.searchParams.set('gps_lon', lon);
            window.parent.location.href = url.href;
        }}
        function showError(error) {{
            const status = document.getElementById('gps-status');
            switch(error.code) {{
                case error.PERMISSION_DENIED:
                    status.innerText = "Location permission denied.";
                    break;
                case error.POSITION_UNAVAILABLE:
                    status.innerText = "Location information is unavailable.";
                    break;
                case error.TIMEOUT:
                    status.innerText = "Request timed out.";
                    break;
                case error.UNKNOWN_ERROR:
                    status.innerText = "An unknown error occurred.";
                    break;
            }}
            status.style.color = "red";
        }}
        </script>
        """, height=120)
        
        # Check if GPS was captured in URL params
        if 'gps_lat' in st.query_params and 'gps_lon' in st.query_params:
            try:
                update_lat = float(st.query_params['gps_lat'])
                update_lon = float(st.query_params['gps_lon'])
                st.success(f"{t['gps_locked']} ({update_lat}, {update_lon})")
            except:
                pass
                
    if new_state_code == "R":
        return_date = st.date_input(t['return_date'], min_value=date.today())
        update_lat = team.get('home_lat') if pd.notna(team.get('home_lat')) else DEFAULT_LAT
        update_lon = team.get('home_lon') if pd.notna(team.get('home_lon')) else DEFAULT_LON
        
    notes = st.text_input(t['notes'], value=team.get('status_notes') or "")
    
    if st.button(t['update_btn'], type="primary", use_container_width=True):
        if new_state_code == "W" and not new_loc:
            st.error(t['error_site'])
        else:
            conn = get_connection()
            c = conn.cursor()
            c.execute("""UPDATE teams 
                         SET state_code=?, status_notes=?, current_location_name=?, return_to_work_date=?, current_lat=?, current_lon=? 
                         WHERE leader_id=?""", 
                      (new_state_code, notes, new_loc, str(return_date) if return_date else None, update_lat, update_lon, team['leader_id']))
            conn.commit()
            release_connection(conn)
            
            conn = get_connection()
            df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=?", conn, params=(team['leader_id'],))
            release_connection(conn)
            st.session_state.leader_data = df.iloc[0].to_dict()
            
            st.success(t['success'])
            st.balloons()
            st.rerun()
            
    st.divider()
    if st.button(t['logout'], use_container_width=True):
        st.query_params.clear()
        st.session_state.leader_logged_in = False
        st.session_state.leader_data = None
        st.rerun()