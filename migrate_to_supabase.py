import sqlite3
import sys, os
sys.path.append(os.path.abspath("core"))
from database import get_connection, init_db
import pandas as pd

def migrate():
    print("Initializing Supabase tables...")
    init_db()
    
    sqlite_path = "data/pm_database.db"
    if not os.path.exists(sqlite_path):
        print("Old SQLite database not found!")
        return

    print("Connecting to old SQLite database...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    
    print("Connecting to new Supabase database...")
    supa_conn = get_connection()
    supa_cur = supa_conn.cursor()

    tables = [
        "materials", 
        "ota_materials", 
        "oa_materials", 
        "lift_crane_items", 
        "teams", 
        "team_history"
    ]

    for table in tables:
        try:
            print(f"Reading {table} from SQLite...")
            df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
            
            if df.empty:
                print(f"Table {table} is empty, skipping.")
                continue
            
            # Clear existing in Supabase just in case
            supa_cur.execute(f"DELETE FROM {table};")
            
            # Insert data into Supabase
            cols = ", ".join([f'"{c}"' for c in df.columns])
            placeholders = ", ".join(["%s" for _ in df.columns])
            sql = f'INSERT INTO {table} ({cols}) VALUES ({placeholders})'
            
            for _, row in df.iterrows():
                # Convert NaN to None
                clean_row = [None if pd.isna(x) else x for x in row]
                supa_cur.execute(sql, tuple(clean_row))
            
            supa_conn.commit()
            print(f"✅ Successfully migrated {len(df)} rows to {table} in Supabase!")
        except Exception as e:
            print(f"❌ Error migrating {table}: {e}")

    sqlite_conn.close()
    supa_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()