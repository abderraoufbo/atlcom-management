import os
import psycopg2
import streamlit as st

@st.cache_resource
def get_connection():
    try:
        db_url = st.secrets["database"]["url"]
    except:
        db_url = os.environ.get("DATABASE_URL")
        
    if not db_url:
        raise ValueError("Database URL not found! Please set it in .streamlit/secrets.toml")
        
    # Connect with TCP Keepalives to prevent Supabase from ever dropping the connection
    conn = psycopg2.connect(
        db_url,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5
    )
    # Set autocommit to True for Supabase pooler compatibility
    conn.autocommit = True
    return conn

def release_connection(conn):
    # Do NOT close the cached connection! Just pass.
    # This keeps the single connection alive forever for all threads.
    pass

@st.cache_resource
def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS materials (id SERIAL PRIMARY KEY, part_number TEXT, material_name TEXT UNIQUE NOT NULL, nature TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ota_materials (id SERIAL PRIMARY KEY, nature TEXT, designation TEXT UNIQUE NOT NULL, pn TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS oa_materials (id SERIAL PRIMARY KEY, material_name TEXT UNIQUE NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lift_crane_items (id SERIAL PRIMARY KEY, item_code TEXT, item_name TEXT UNIQUE NOT NULL, item_by TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS teams (
        id SERIAL PRIMARY KEY,
        team_name TEXT UNIQUE NOT NULL,
        leader_id TEXT,
        leader_name TEXT,
        skills TEXT,
        wilaya TEXT,
        home_lat REAL,
        home_lon REAL,
        home_location_name TEXT,
        current_lat REAL,
        current_lon REAL,
        current_location_name TEXT,
        region TEXT,
        current_project TEXT,
        status TEXT DEFAULT 'Available',
        status_notes TEXT,
        state_code TEXT DEFAULT 'S',
        start_date TEXT,
        return_to_work_date TEXT,
        notes TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS team_history (
        id SERIAL PRIMARY KEY,
        team_name TEXT,
        activity_type TEXT,
        location TEXT,
        start_date TEXT,
        end_date TEXT,
        duration_days REAL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS generated_documents (
        id SERIAL PRIMARY KEY,
        doc_type TEXT,
        client TEXT,
        site_code TEXT,
        file_name TEXT,
        generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.close()
    print("Supabase PostgreSQL initialized successfully with Keepalives!")

if __name__ == "__main__":
    init_db()