import streamlit as st
import sqlite3
import pandas as pd
import base64
import io
from PIL import Image
from datetime import date, datetime
import sys, os

sys.path.append(os.path.abspath("core"))
from database import get_connection, release_connection

def compress_image(uploaded_file, max_size=800):
    img = Image.open(uploaded_file)
    img.thumbnail((max_size, max_size))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return base64.b64encode(buf.getvalue()).decode()

def render_portal():
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none !important; }
        .block-container { max-width: 700px !important; margin: 0 auto !important; padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🚚 Driver Task Portal")
    
    if 'driver_logged_in' not in st.session_state: st.session_state.driver_logged_in = False
    
    if not st.session_state.driver_logged_in:
        st.subheader("Login")
        driver_name = st.text_input("Enter your Name")
        if st.button("Login", type="primary", use_container_width=True):
            st.session_state.driver_logged_in = True
            st.session_state.driver_name = driver_name
            st.rerun()
        return

    st.success(f"Welcome, {st.session_state.driver_name}")
    st.write("#### Open Tasks Needing Action")
    
    conn = get_connection()
    df_tasks = pd.read_sql_query("SELECT * FROM tasks WHERE status='Open' ORDER BY created_at DESC", conn)
    release_connection(conn)
    
    if df_tasks.empty:
        st.info("No open tasks right now. Good job!")
    else:
        for _, task in df_tasks.iterrows():
            with st.expander(f"{task['task_type']} - {task['team_name']} ({task['created_at'].strftime('%H:%M %d-%b')})"):
                st.write(f"**Location:** Lat {task['lat']:.4f}, Lon {task['lon']:.4f}")
                st.write(f"**Notes:** {task['notes'] or 'N/A'}")
                
                # Show Leader's Photo
                if task['photo_base64']:
                    img_data = base64.b64decode(task['photo_base64'])
                    st.image(io.BytesIO(img_data), caption="Proof from Team Leader", use_container_width=True)
                
                # Map Link
                gmaps_url = f"https://www.google.com/maps?q={task['lat']},{task['lon']}"
                st.markdown(f"[📍 Open in Google Maps]({gmaps_url})")
                
                st.divider()
                st.write("**Complete this task:**")
                comp_file = st.file_uploader("Upload Completion Photo", type=['jpg', 'jpeg', 'png'], key=f"comp_{task['id']}")
                
                if st.button("✅ Mark as Completed", key=f"done_{task['id']}", type="primary", use_container_width=True):
                    if not comp_file:
                        st.warning("Please upload a completion photo first.")
                    else:
                        comp_b64 = compress_image(comp_file)
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE tasks SET status='Completed', driver_id=%s, completion_photo_base64=%s, completed_at=CURRENT_TIMESTAMP WHERE id=%s",
                                  (st.session_state.driver_name, comp_b64, task['id']))
                        conn.commit()
                        release_connection(conn)
                        st.success("Task marked as completed! The manager has been notified.")
                        st.rerun()

    st.divider()
    if st.button("Logout", use_container_width=True):
        st.session_state.driver_logged_in = False
        st.rerun()