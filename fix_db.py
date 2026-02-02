import sqlite3

# Connect to the database
db_path = "database/marco_interviews.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"🔧 Connecting to {db_path}...")

try:
    # 1. Add the missing 'updated_at' column (Safe Mode)
    cursor.execute("ALTER TABLE candidates ADD COLUMN updated_at DATETIME")
    conn.commit()
    print("✅ Success! Added 'updated_at' column.")
except Exception as e:
    if "duplicate column name" in str(e):
        print("✅ Good news: The column already exists!")
    else:
        print(f"ℹ️ Status: {e}")

conn.close()
