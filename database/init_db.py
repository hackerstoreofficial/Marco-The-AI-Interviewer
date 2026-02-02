"""
Marco AI Interview Simulator - Database Initialization Script
This script creates and initializes the SQLite database with the schema.
"""

import sqlite3
import os
from pathlib import Path

# Database configuration
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "marco_interviews.db"
SCHEMA_PATH = DB_DIR / "schema.sql"


def init_database():
    """Initialize the database with schema from schema.sql"""
    
    print(f"[DATABASE] Initializing Marco Interview Database...")
    print(f"[DATABASE] Location: {DB_PATH}")
    
    # Check if schema file exists
    if not SCHEMA_PATH.exists():
        print(f"[ERROR] Schema file not found at {SCHEMA_PATH}")
        return False
    
    try:
        # Connect to database (creates file if doesn't exist)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Read and execute schema
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as schema_file:
            schema_sql = schema_file.read()
            cursor.executescript(schema_sql)
        
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"[SUCCESS] Database initialized successfully!")
        print(f"[INFO] Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False


def reset_database():
    """Delete existing database and reinitialize"""
    if DB_PATH.exists():
        print(f"[WARNING] Deleting existing database at {DB_PATH}")
        os.remove(DB_PATH)
    return init_database()


if __name__ == "__main__":
    import sys
    
    # Check for reset flag
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        init_database()
