import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import sys, os

sys.path.append(os.path.abspath("core"))
from database import get_connection
from dispatch_tool import ALGERIAN_WILAYAS, DEFAULT_LAT, DEFAULT_LON

def render_portal():
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none !important; }
        .block-container { max-width: 600px !important; margin: 0 auto !important; padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📡 Team Leader Portal")
    
    # --- AUTO LOGIN FROM URL ---
    query_params = st.query_params
    if 'lid' in query_params and not st.session_state.get('leader_logged_in'):
        leader_id = query_params['lid']
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=?", conn, params=(leader_id,))
        conn.close()
        if not df.empty:
            st.session_state.leader_logged_in = True
            st.session_state.leader_data = df.iloc[0].to_dict()

    if 'leader_logged_in' not in st.session_state:
        st.session_state.leader_logged_in = False
        
    # --- LOGIN SCREEN ---
    if not st.session_state.leader_logged_in:
        st.subheader("Login")
        leader_id = st.text_input("Enter your Team Leader ID")
        
        if st.button("Login", type="primary", use_container_width=True):
            conn = get_connection()
            df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=?", conn, params=(leader_id,))
            conn.close()
            if not df.empty:
                # Save ID to URL so they never have to login again on this device
                st.query_params['lid'] = leader_id
                st.session_state.leader_logged_in = True
                st.session_state.leader_data = df.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Invalid Leader ID. Please check with your manager.")
        return

    # --- DASHBOARD FOR LEADER ---
    team = st.session_state.leader_data
    st.success(f"Welcome, {team['leader_name']} ({team['team_name']})")
    
    current_state = team.get('state_code') or 'S'
    state_colors = {"W": "🟢 Working", "R": "🟠 Resting", "S": "🔵 Stand-by", "T": "🔴 On Road", "P": "🔴 Urgency"}
    st.info(f"Current Status: **{state_colors.get(current_state, 'Unknown')}**\n\nLocation: **{team.get('current_location_name') or 'N/A'}**")
    
    st.divider()
    st.subheader("Update Your Status")
    
    new_state = st.selectbox("New State", ["W (Working)", "R (Resting)", "S (Stand-by)", "T (On road)", "P (Urgency)"])
    new_loc = ""
    return_date = None
    update_lat, update_lon = None, None
    
    if new_state == "W (Working)":
        new_loc = st.text_input("Site ID / Current Location Name *", value=team.get('current_location_name') or "")
        new_wilaya = st.selectbox("Select Wilaya (For Map Pin)", list(ALGERIAN_WILAYAS.keys()), index=list(ALGERIAN_WILAYAS.keys()).index(team.get('wilaya')) if team.get('wilaya') in ALGERIAN_WILAYAS else 0)
        update_lat, update_lon = ALGERIAN_WILAYAS[new_wilaya]
        
    if new_state == "R (Resting)":
        return_date = st.date_input("Planned Return to Work Date", min_value=date.today())
        update_lat = team.get('home_lat') if pd.notna(team.get('home_lat')) else DEFAULT_LAT
        update_lon = team.get('home_lon') if pd.notna(team.get('home_lon')) else DEFAULT_LON
        
    notes = st.text_input("Notes (Optional)", value=team.get('status_notes') or "")
    
    if st.button("🚀 Update Status", type="primary", use_container_width=True):
        if new_state == "W (Working)" and not new_loc:
            st.error("Please enter the Site ID.")
        else:
            state_letter = new_state[0]
            conn = get_connection()
            c = conn.cursor()
            c.execute("""UPDATE teams 
                         SET state_code=?, status_notes=?, current_location_name=?, return_to_work_date=?, current_lat=?, current_lon=? 
                         WHERE leader_id=?""", 
                      (state_letter, notes, new_loc, str(return_date) if return_date else None, update_lat, update_lon, team['leader_id']))
            conn.commit()
            conn.close()
            
            conn = get_connection()
            df = pd.read_sql_query("SELECT * FROM teams WHERE leader_id=?", conn, params=(team['leader_id'],))
            conn.close()
            st.session_state.leader_data = df.iloc[0].to_dict()
            
            st.success("Status updated successfully! The General Manager has been notified.")
            st.balloons()
            st.rerun()
            
    st.divider()
    if st.button("Logout", use_container_width=True):
        # Clear URL params and session on logout
        st.query_params.clear()
        st.session_state.leader_logged_in = False
        st.session_state.leader_data = None
        st.rerun()