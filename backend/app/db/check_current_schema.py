# check_current_schema.py
# Run this to see what columns already exist

import sqlite3
import os
from pathlib import Path

# Adjust this path to your actual database file
DB_PATH = "dev.db"  # or wherever your SQLite file is

def check_table_schema(db_path, table_name):
    """Check the current schema of a table."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print(f"\n=== Current schema for '{table_name}' table ===")
        if columns:
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - nullable: {not col[3]} - default: {col[4]}")
        else:
            print(f"  Table '{table_name}' does not exist")
    
    except sqlite3.Error as e:
        print(f"Error checking {table_name}: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    tables_to_check = [
        "users", 
        "chat_sessions", 
        "messages", 
        "unanswered_queries"
    ]
    
    for table in tables_to_check:
        check_table_schema(DB_PATH, table)