#!/usr/bin/env python3
"""Check database for category data."""

import sqlite3
import os

def check_messages_table():
    """Check the messages table for category data."""
    
    db_path = "dev.db"
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check table schema
        cursor.execute("PRAGMA table_info(messages);")
        columns = cursor.fetchall()
        print("=== Messages table schema ===")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - nullable: {not col[3]}")
        
        # Check recent messages
        cursor.execute("""
            SELECT id, role, content, category, created_at 
            FROM messages 
            ORDER BY id DESC 
            LIMIT 10
        """)
        messages = cursor.fetchall()
        
        print("\n=== Recent messages ===")
        for msg in messages:
            print(f"ID: {msg[0]}, Role: {msg[1]}, Category: '{msg[3]}', Content: {msg[2][:50]}...")
        
        # Check unanswered queries
        cursor.execute("""
            SELECT id, text, category, created_at 
            FROM unanswered_queries 
            ORDER BY id DESC 
            LIMIT 5
        """)
        unanswered = cursor.fetchall()
        
        print("\n=== Recent unanswered queries ===")
        for uq in unanswered:
            print(f"ID: {uq[0]}, Category: '{uq[2]}', Text: {uq[1][:50]}...")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_messages_table() 