import psycopg2
import streamlit as st
import os
import sys

sys.path.append(os.path.abspath("core"))
from database import get_connection, release_connection

def fix_sequences():
    print("Connecting to Supabase...")
    conn = get_connection()
    c = conn.cursor()
    
    tables = ["clients", "materials", "ota_materials", "oa_materials", "lift_crane_items", "teams", "team_history", "generated_documents", "tasks"]
    
    for table in tables:
        try:
            # This command resets the auto-increment sequence to MAX(id) + 1
            c.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), (SELECT MAX(id) FROM {table}));")
            print(f"✅ Sequence fixed for table: {table}")
        except Exception as e:
            print(f"⚠️ Could not fix sequence for {table} (might be empty or not exist): {e}")
            
    conn.commit()
    release_connection(conn)
    print("\nAll sequences fixed! You can now add teams without errors.")

if __name__ == "__main__":
    fix_sequences()