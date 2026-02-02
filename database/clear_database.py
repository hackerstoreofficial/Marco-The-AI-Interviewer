"""
Marco AI Interview Simulator - Clear Database Script
This script safely deletes and reinitializes the database.
WARNING: This will delete ALL interview data!
"""

import sqlite3
import os
from pathlib import Path
import sys

# Database configuration
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "marco_interviews.db"
SCHEMA_PATH = DB_DIR / "schema.sql"


def get_database_stats():
    """Get statistics about the current database."""
    if not DB_PATH.exists():
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        stats = {}
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get row counts for each table
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count
        
        conn.close()
        return stats
        
    except Exception as e:
        print(f"[ERROR] Could not read database stats: {e}")
        return None


def clear_database(force=False):
    """
    Clear the database by deleting and reinitializing it.
    
    Args:
        force: If True, skip confirmation prompt
    """
    print("\n" + "=" * 70)
    print("🗑️  CLEAR DATABASE - Marco AI Interview Simulator")
    print("=" * 70)
    
    # Check if database exists
    if not DB_PATH.exists():
        print(f"\n✅ Database does not exist at: {DB_PATH}")
        print("Nothing to clear. Run init_db.py to create a new database.")
        return True
    
    # Show current database stats
    print(f"\n📊 Current Database: {DB_PATH}")
    print(f"📏 File size: {DB_PATH.stat().st_size / 1024:.2f} KB")
    
    stats = get_database_stats()
    if stats:
        print(f"\n📋 Current Data:")
        total_records = 0
        for table, count in stats.items():
            print(f"   - {table}: {count} records")
            total_records += count
        print(f"\n   Total: {total_records} records across {len(stats)} tables")
    
    # Confirmation prompt (unless force flag is set)
    if not force:
        print("\n" + "=" * 70)
        print("⚠️  WARNING: This will DELETE ALL DATA!")
        print("=" * 70)
        print("This action cannot be undone. All interview data will be lost.")
        print("The database will be recreated with an empty schema.")
        
        confirmation = input("\nType 'DELETE' to confirm (or anything else to cancel): ").strip()
        
        if confirmation != "DELETE":
            print("\n❌ Operation cancelled. Database was not modified.")
            return False
    
    # Delete the database file
    print("\n" + "=" * 70)
    print("🗑️  Deleting database...")
    print("=" * 70)
    
    try:
        os.remove(DB_PATH)
        print(f"✅ Database file deleted: {DB_PATH}")
    except Exception as e:
        print(f"❌ Error deleting database: {e}")
        return False
    
    # Reinitialize with schema
    print("\n" + "=" * 70)
    print("🔄 Reinitializing database...")
    print("=" * 70)
    
    if not SCHEMA_PATH.exists():
        print(f"❌ Schema file not found at {SCHEMA_PATH}")
        return False
    
    try:
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
        
        print(f"\n✅ Database reinitialized successfully!")
        print(f"📋 Created {len(tables)} empty tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ DATABASE CLEARED AND RESET SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n📁 Clean database ready at: {DB_PATH}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def show_help():
    """Show help information."""
    print("\n" + "=" * 70)
    print("📖 CLEAR DATABASE SCRIPT - Help")
    print("=" * 70)
    print("\nUsage:")
    print("  python clear_database.py           - Interactive mode (with confirmation)")
    print("  python clear_database.py --force   - Force clear (no confirmation)")
    print("  python clear_database.py --help    - Show this help message")
    print("\nDescription:")
    print("  This script deletes the existing database and creates a fresh one")
    print("  with the schema from schema.sql. All data will be lost!")
    print("\nSafety:")
    print("  - Interactive mode requires typing 'DELETE' to confirm")
    print("  - Shows current database statistics before deletion")
    print("  - Automatically reinitializes with clean schema")
    print("=" * 70)


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            show_help()
            sys.exit(0)
        elif sys.argv[1] == "--force" or sys.argv[1] == "-f":
            print("\n⚡ Force mode enabled - skipping confirmation")
            clear_database(force=True)
        else:
            print(f"\n❌ Unknown argument: {sys.argv[1]}")
            print("Use --help to see available options")
            sys.exit(1)
    else:
        # Interactive mode
        clear_database(force=False)
