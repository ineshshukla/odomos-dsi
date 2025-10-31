"""
Migration script to add clinic_name column to documents table
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path(__file__).parent / "database.db"
    
    if not db_path.exists():
        print("❌ Database not found. Nothing to migrate.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "clinic_name" in columns:
            print("✅ clinic_name column already exists. No migration needed.")
            return
        
        # Add the column
        print("🔧 Adding clinic_name column to documents table...")
        cursor.execute("ALTER TABLE documents ADD COLUMN clinic_name VARCHAR(255)")
        conn.commit()
        print("✅ Successfully added clinic_name column!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
