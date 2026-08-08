import os
import psycopg2
from psycopg2 import pool
import streamlit as st

# Global connection pool
_connection_pool = None

def init_pool():
    global _connection_pool
    if _connection_pool is None or _connection_pool.closed:
        try:
            db_url = st.secrets["database"]["url"]
        except:
            db_url = os.environ.get("DATABASE_URL")
            
        if not db_url:
            raise ValueError("Database URL not found! Please set it in .streamlit/secrets.toml")
            
        # Create a pool with min 1 and max 5 connections
        _connection_pool = pool.SimpleConnectionPool(1, 5, db_url)

def get_connection():
    init_pool()
    # Get a connection from the pool
    return _connection_pool.getconn()

def release_connection(conn):
    init_pool()
    if conn and not _connection_pool.closed:
        # Put the connection back in the pool for the next person to use
        _connection_pool.putconn(conn)

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

    conn.commit()
    release_connection(conn)
    print("Supabase PostgreSQL initialized successfully!")