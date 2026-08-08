import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
import base64
import io
import re
import urllib.request
from PIL import Image
from datetime import date, datetime
import sys, os

sys.path.append(os.path.abspath("core"))
from database import get_connection, release_connection
from tools.dispatch_tool import ALGERIAN_WILAYAS, DEFAULT_LAT, DEFAULT_LON

# Helper to compress and resize images before saving to database
def compress_image(uploaded_file, max_size=800, quality=70):
    try:
        img = Image.open(uploaded_file)
        
        # Convert to RGB to fix PNG transparency errors (RGBA cannot be saved as JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Resize the image to max_size (e.g., 800x800) to reduce file size
        img.thumbnail((max_size, max_size))
        
        # Compress and save to memory buffer
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        
        # Encode to base64 string
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

# Helper to extract coordinates from Google Maps link, raw coords, or shortlinks
def extract_coords_from_link(link):
    if not link: return None, None
    
    link = link.strip()
    
    # 1. Check for plain raw coordinates "36.540586, 2.983051"
    raw_match = re.match(r'^\s*(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)\s*$', link)
    if raw_match:
        return float(raw_match.group(1)), float(raw_match.group(2))
        
    # 2. Check for Plus Codes and reject them gracefully
    if '+' in link and ',' in link and 'http' not in link:
        return "plus_code", None
        
    # 3. If it's a shortlink, resolve it to get the full URL
    if 'goo.gl' in link or 'maps.app.goo.gl' in link:
        try:
            req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            resp = urllib.request.urlopen(req, timeout=8)
            link = resp.geturl() # Gets the final redirected URL
        except:
            pass
            
    # 4. Match standard URL patterns
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', link)
    if match: return float(match.group(1)), float(match.group(2))
    match = re.search(r'q=(-?\d+\.\d+),(-?\d+\.\d+)', link)
    if match: return float(match.group(1)), float(match.group(2))
    match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', link)
    if match: return float(match.group(1)), float(match.group(2))
    match = re.search(r'center=(-?\d+\.\d+),(-?\d+\.\d+)', link)
    if match: return float(match.group(1)), float(match.group(2))
    
    # 5. Fallback: find any two decimal numbers separated by comma in the URL
    match = re.search(r'(-?\d{1,3}\.\d{4,})\s*,\s*(-?\d{1,3}\.\d{4,})', link)
    if match: return float(match.group(1)), float(match.group(2))
    
    return None, None

portal_translations = {
    'EN': {
        'title': "📡 Team Leader Portal", 'language': "Language", 'login': "Login",
        'enter_id': "Enter your Team Leader ID", 'invalid': "Invalid Leader ID.",
        'welcome': "Welcome,", 'current_status': "Current Status", 'location': "Location",
        'update_status': "Update Your Status", 'new_state': "New State",
        'site_id': "Site ID / Current Location Name *", 'select_wilaya': "Select Wilaya (For Map Pin)",
        'return_date': "Planned Return to Work Date", 'notes': "Notes (Optional)",
        'update_btn': "🚀 Update Status", 'error_site': "Please enter the Site ID.",
        'success': "Status updated successfully!", 'logout': "Logout",
        'get_gps': "📍 Get My Exact GPS", 'gps_locked': "Exact GPS Locked!",
        'report_task': "📋 Report Task / Need Action",
        'task_type': "Task Type", 'task_notes': "Additional Details / Notes",
        'task_photo': "Upload Photo Proof (Optional)", 'submit_task': "✅ Submit Task",
        'task_success': "Task submitted! The driver team has been notified.",
        'menu_status': "Status", 'menu_task': "Report Task",
        'paste_link': "Or Paste Google Maps Link / Coordinates Here",
        'link_help': "If GPS button fails: Open Google Maps, tap your blue dot, tap 'Share', copy the link and paste it here. (You can also type coordinates like: 36.540, 2.983)",
        'invalid_link': "Could not find coordinates. Please do not use Plus Codes (GXRM+5CM). Copy the share link or type coordinates manually.",
        'states': {"W": "🟢 Working", "R": "🟠 Resting", "S": "🔵 Stand-by", "T": "🔴 On Road", "P": "🔴 Urgency"}
    },
    'FR': {
        'title': "📡 Portail Chef d'Équipe", 'language': "Langue", 'login': "Connexion",
        'enter_id': "Entrez votre ID", 'invalid': "ID invalide.", 'welcome': "Bienvenue,",
        'current_status': "Statut Actuel", 'location': "Emplacement", 'update_status': "Mettre à jour",
        'new_state': "Nouvel État", 'site_id': "ID du Site *", 'select_wilaya': "Sélectionner Wilaya",
        'return_date': "Date de Retour", 'notes': "Notes", 'update_btn': "🚀 Mettre à jour",
        'error_site': "Veuillez entrer l'ID du site.", 'success': "Succès !", 'logout': "Déconnexion",
        'get_gps': "📍 Obtenir mon GPS", 'gps_locked': "GPS verrouillé !",
        'report_task': "📋 Signaler une Tâche",
        'task_type': "Type de Tâche", 'task_notes': "Détails / Notes",
        'task_photo': "Importer une Photo (Optionnel)", 'submit_task': "✅ Soumettre",
        'task_success': "Tâche soumise ! Les conducteurs ont été notifiés.",
        'menu_status': "Statut", 'menu_task': "Signaler Tâche",
        'paste_link': "Ou collez le lien Google Maps / Coordonnées ici",
        'link_help': "Si le GPS échoue : Ouvrez Google Maps, touchez votre point bleu, 'Partager', copiez le lien et collez-le ici.",
        'invalid_link': "Coordonnées introuvables. N'utilisez pas de Plus Codes. Copiez le lien de partage ou tapez les coordonnées.",
        'states': {"W": "🟢 En Travail", "R": "🟠 En Repos", "S": "🔵 Disponible", "T": "🔴 En Route", "P": "🔴 Urgence"}
    },
    'AR': {
        'title': "📡 بوابة قادة الفرق", 'language': "اللغة", 'login': "تسجيل الدخول",
        'enter_id': "أدخل معرف القائد", 'invalid': "معرف غير صالح.", 'welcome': "مرحباً،",
        'current_status': "الحالة الحالية", 'location': "الموقع", 'update_status': "تحديث الحالة",
        'new_state': "الحالة الجديدة", 'site_id': "رقم الموقع *", 'select_wilaya': "اختر الولاية",
        'return_date': "تاريخ العودة", 'notes': "ملاحظات", 'update_btn': "🚀 تحديث",
        'error_site': "الرجاء إدخال رقم الموقع.", 'success': "تم التحديث بنجاح!", 'logout': "خروج",
        'get_gps': "📍 احصل على موقعي", 'gps_locked': "تم تحديد الموقع!",
        'report_task': "📋 الإبلاغ عن مهمة",
        'task_type': "نوع المهمة", 'task_notes': "تفاصيل إضافية / ملاحظات",
        'task_photo': "رفع صورة (اختياري)", 'submit_task': "✅ إرسال المهمة",
        'task_success': "تم إرسال المهمة! تم إبلاغ السائقين.",
        'menu_status': "الحالة", 'menu_task': "إبلاغ عن مهمة",
        'paste_link': "أو الصق رابط خرائط جوجل / الإحداثيات هنا",
        'link_help': "إذا فشل زر تحديد الموقع: افتح خرائط جوجل، انقر على النقطة الزرقاء، 'مشاركة'، انسخ الرابط والصقه هنا.",
        'invalid_link': "تعذر العثور على الإحداثيات. لا تستخدم رموز Plus Codes. انسخ رابط المشاركة أو اكتب الإحداثيات.",
        'states': {"W": "🟢 يعمل", "R": "🟠 راحة", "S": "🔵 مستعد", "T": "🔴 على الطريق", "P": "🔴 طارئ"}
    }
}

def render_portal():
    if 'portal_lang' not in st.session_state: st.session_state.portal_lang = 'EN'
    t = portal_translations[st.session_state.portal_lang]
    is_ar = st.session_state.portal_lang == 'AR'
    direction = "rtl" if is_ar else "ltr"
    text_align = "right" if is_ar else "left"
    
    # Initialize menu state (0 = Status, 1 = Task)
    if 'portal_menu_idx' not in st.session_state: st.session_state.portal_menu_idx = 0
    if 'show_task_success' not in st.session_state: st.session_state.show_task_success = False
    
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

    if 'leader_logged_in' not in st.session_state: st.session_state.leader_logged_in = False
    if not st.session_state.leader_logged_in:
        st.subheader(t['login'])
        leader_id = st.text_input(t['enter_id'])
        if st.button(t['login'], type="primary", use_container_width=True):
            conn = get_connection()
            df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=%(lid)s", conn, params={"lid": leader_id})
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
    
    # Menu Selection
    menu_idx = st.radio("Menu", [0, 1], format_func=lambda x: t['menu_status'] if x == 0 else t['menu_task'], horizontal=True, label_visibility="collapsed", index=st.session_state.portal_menu_idx)
    st.session_state.portal_menu_idx = menu_idx
    
    if menu_idx == 0:
        # Show success message if we just redirected from task submission
        if st.session_state.show_task_success:
            st.success(t['task_success'])
            st.session_state.show_task_success = False # Clear it so it only shows once
            
        current_state = team.get('state_code') or 'S'
        st.info(f"{t['current_status']}: **{t['states'].get(current_state, 'Unknown')}**\n\n{t['location']}: **{team.get('current_location_name') or 'N/A'}**")
        st.divider()
        st.subheader(t['update_status'])
        
        state_options = ["W", "R", "S", "T", "P"]
        state_labels = [f"{s} - {t['states'][s]}" for s in state_options]
        selected_idx = st.selectbox(t['new_state'], range(len(state_labels)), format_func=lambda x: state_labels[x])
        new_state_code = state_options[selected_idx]
        
        new_loc, return_date, update_lat, update_lon = "", None, None, None
        
        if new_state_code == "W":
            new_loc = st.text_input(t['site_id'], value=team.get('current_location_name') or "")
            new_wilaya = st.selectbox(t['select_wilaya'], list(ALGERIAN_WILAYAS.keys()), index=list(ALGERIAN_WILAYAS.keys()).index(team.get('wilaya')) if team.get('wilaya') in ALGERIAN_WILAYAS else 0)
            update_lat, update_lon = ALGERIAN_WILAYAS[new_wilaya]
            
            # --- FAST GPS BUTTON ---
            st.markdown(f"##### 📍 {t['get_gps']}")
            st.markdown(f"""
            <iframe srcdoc="
                <html><body style='margin:0;padding:0;'>
                <button onclick='getStatusGPS()' style='width:100%; padding:12px; border-radius:8px; border:none; background:linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); color:white; font-weight:600; cursor:pointer;'>{t['get_gps']}</button>
                <p id='status-msg' style='text-align:center; font-family:sans-serif; margin-top:5px; font-weight:bold;'></p>
                <script>
                    function getStatusGPS() {{
                        const msg = document.getElementById('status-msg');
                        msg.innerText = 'Locating... Please wait';
                        msg.style.color = 'blue';
                        if (!navigator.geolocation) {{
                            msg.innerText = 'GPS not supported. Use link below.';
                            msg.style.color = 'red'; return;
                        }}
                        navigator.geolocation.getCurrentPosition(
                            (pos) => {{
                                const lat = pos.coords.latitude;
                                const lon = pos.coords.longitude;
                                const url = new URL(window.parent.location.href);
                                url.searchParams.set('gps_lat', lat);
                                url.searchParams.set('gps_lon', lon);
                                window.parent.location.href = url.href;
                            }},
                            (err) => {{
                                if (err.code === 1) msg.innerText = 'Permission Denied. Use link below.';
                                else if (err.code === 3) msg.innerText = 'Timeout. Use link below.';
                                else msg.innerText = 'Error. Use link below.';
                                msg.style.color = 'red';
                            }},
                            {{ enableHighAccuracy: false, timeout: 8000, maximumAge: 0 }}
                        );
                    }}
                </script>
                </body></html>"
                allow="geolocation" style="width:100%; height:90px; border:none;"></iframe>
            """, unsafe_allow_html=True)
            
            if 'gps_lat' in st.query_params:
                update_lat = float(st.query_params['gps_lat'])
                update_lon = float(st.query_params['gps_lon'])
                st.success(f"📍 {t['gps_locked']}")
                
            # --- LINK FALLBACK ---
            st.caption(t['link_help'])
            maps_link = st.text_input(t['paste_link'], key="maps_link_status", label_visibility="collapsed")
            if maps_link:
                p_lat, p_lon = extract_coords_from_link(maps_link)
                if p_lat == "plus_code":
                    st.error(t['invalid_link'])
                elif p_lat is not None:
                    update_lat = p_lat
                    update_lon = p_lon
                    st.success(f"📍 {t['gps_locked']} ({update_lat}, {update_lon})")

        if new_state_code == "R":
            return_date = st.date_input(t['return_date'], min_value=date.today())
            update_lat = team.get('home_lat') if pd.notna(team.get('home_lat')) else DEFAULT_LAT
            update_lon = team.get('home_lon') if pd.notna(team.get('home_lon')) else DEFAULT_LON
            
        notes = st.text_input(t['notes'], value=team.get('status_notes') or "")
        if st.button(t['update_btn'], type="primary", use_container_width=True):
            if new_state_code == "W" and maps_link and update_lat == ALGERIAN_WILAYAS[new_wilaya][0]:
                with st.spinner("Reading map link..."):
                    p_lat, p_lon = extract_coords_from_link(maps_link)
                    if p_lat and p_lat != "plus_code":
                        update_lat, update_lon = p_lat, p_lon

            if new_state_code == "W" and not new_loc:
                st.error(t['error_site'])
            else:
                conn = get_connection()
                c = conn.cursor()
                c.execute("UPDATE teams SET state_code=%s, status_notes=%s, current_location_name=%s, return_to_work_date=%s, current_lat=%s, current_lon=%s WHERE leader_id=%s", (new_state_code, notes, new_loc, str(return_date) if return_date else None, update_lat, update_lon, team['leader_id']))
                conn.commit()
                release_connection(conn)
                st.success(t['success'])
                st.rerun()

    elif menu_idx == 1:
        st.subheader(t['report_task'])
        task_type = st.selectbox(t['task_type'], ["🧹 Clean Up", "📦 Material Pick Up", "🛠️ Extra Work", "💧 Waterproofing"])
        task_notes = st.text_area(t['task_notes'], key="task_notes_input")
        uploaded_file = st.file_uploader(t['task_photo'], type=['jpg', 'jpeg', 'png'])
        
        # --- FAST GPS BUTTON ---
        st.markdown(f"##### 📍 {t['get_gps']}")
        st.markdown(f"""
            <iframe srcdoc="
                <html><body style='margin:0;padding:0;'>
                <button onclick='getTaskGPS()' style='width:100%; padding:12px; border-radius:8px; border:none; background:#0078D7; color:white; font-weight:600; cursor:pointer;'>📍 {t['get_gps']}</button>
                <p id='task-msg' style='text-align:center; font-family:sans-serif; margin-top:5px; font-weight:bold;'></p>
                <script>
                    function getTaskGPS() {{
                        const msg = document.getElementById('task-msg');
                        msg.innerText = 'Locating... Please wait';
                        msg.style.color = 'blue';
                        if (!navigator.geolocation) {{
                            msg.innerText = 'GPS not supported. Use link below.';
                            msg.style.color = 'red'; return;
                        }}
                        navigator.geolocation.getCurrentPosition(
                            (pos) => {{
                                const lat = pos.coords.latitude;
                                const lon = pos.coords.longitude;
                                const url = new URL(window.parent.location.href);
                                url.searchParams.set('task_lat', lat);
                                url.searchParams.set('task_lon', lon);
                                window.parent.location.href = url.href;
                            }},
                            (err) => {{
                                if (err.code === 1) msg.innerText = 'Permission Denied. Use link below.';
                                else if (err.code === 3) msg.innerText = 'Timeout. Use link below.';
                                else msg.innerText = 'Error. Use link below.';
                                msg.style.color = 'red';
                            }},
                            {{ enableHighAccuracy: false, timeout: 8000, maximumAge: 0 }}
                        );
                    }}
                </script>
                </body></html>"
                allow="geolocation" style="width:100%; height:90px; border:none;"></iframe>
        """, unsafe_allow_html=True)
        
        task_lat, task_lon = None, None
        if 'task_lat' in st.query_params:
            task_lat = float(st.query_params['task_lat'])
            task_lon = float(st.query_params['task_lon'])
            st.success(f"📍 {t['gps_locked']}")
            
        # --- LINK FALLBACK ---
        st.caption(t['link_help'])
        maps_link_task = st.text_input(t['paste_link'], key="maps_link_task", label_visibility="collapsed")

        if st.button(t['submit_task'], type="primary", use_container_width=True):
            # Resolve link if button didn't work
            if task_lat is None and maps_link_task:
                with st.spinner("Reading map link..."):
                    task_lat, task_lon = extract_coords_from_link(maps_link_task)
                    
            if task_lat == "plus_code":
                st.error(t['invalid_link'])
            elif task_lat is None:
                st.error("Location is required. Please use the GPS button or paste a valid Google Maps link.")
            else:
                # Compress image before saving
                photo_b64 = compress_image(uploaded_file) if uploaded_file else None
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO tasks (task_type, leader_id, team_name, lat, lon, notes, photo_base64) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                          (task_type, team['leader_id'], team['team_name'], task_lat, task_lon, task_notes, photo_b64))
                conn.commit()
                release_connection(conn)
                
                # --- AUTOMATIC REDIRECT TO STATUS SCREEN ---
                st.session_state.show_task_success = True
                st.session_state.portal_menu_idx = 0 # Switch back to Status tab
                
                # Clear form fields
                st.session_state.task_notes_input = ""
                st.session_state.maps_link_task = ""
                
                # Clear GPS from URL
                if 'task_lat' in st.query_params: del st.query_params['task_lat']
                if 'task_lon' in st.query_params: del st.query_params['task_lon']
                
                st.rerun()

    st.divider()
    if st.button(t['logout'], use_container_width=True):
        st.query_params.clear()
        st.session_state.leader_logged_in = False
        st.session_state.leader_data = None
        st.rerun()