import sqlite3
import os
from pathlib import Path

DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "pm_database.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS materials (id INTEGER PRIMARY KEY AUTOINCREMENT, part_number TEXT, material_name TEXT UNIQUE NOT NULL, nature TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ota_materials (id INTEGER PRIMARY KEY AUTOINCREMENT, nature TEXT, designation TEXT UNIQUE NOT NULL, pn TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS oa_materials (id INTEGER PRIMARY KEY AUTOINCREMENT, material_name TEXT UNIQUE NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lift_crane_items (id INTEGER PRIMARY KEY AUTOINCREMENT, item_code TEXT, item_name TEXT UNIQUE NOT NULL, item_by TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    
    # NEW: Team History Table
    c.execute('''CREATE TABLE IF NOT EXISTS team_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name TEXT,
        activity_type TEXT,
        location TEXT,
        start_date TEXT,
        end_date TEXT,
        duration_days REAL
    )''')

    def add_column_if_missing(cursor, table_name, col_name, col_type):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")

    for col, typ in [("leader_id", "TEXT"), ("leader_name", "TEXT"), ("wilaya", "TEXT"), ("region", "TEXT"), 
                     ("current_project", "TEXT"), ("status_notes", "TEXT"), ("state_code", "TEXT"),
                     ("home_lat", "REAL"), ("home_lon", "REAL"), ("home_location_name", "TEXT"), 
                     ("start_date", "TEXT"), ("return_to_work_date", "TEXT")]:
        add_column_if_missing(c, "teams", col, typ)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()