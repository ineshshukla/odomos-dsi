"""
Migration script to add review_status fields to predictions table
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path(__file__).parent / "predictions.db"
    
    if not db_path.exists():
        print("❌ Database not found. Nothing to migrate.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(predictions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        columns_to_add = []
        if "review_status" not in columns:
            columns_to_add.append(("review_status", "VARCHAR(50) DEFAULT 'New'"))
        if "coordinator_notes" not in columns:
            columns_to_add.append(("coordinator_notes", "TEXT"))
        if "reviewed_by" not in columns:
            columns_to_add.append(("reviewed_by", "VARCHAR(100)"))
        if "reviewed_at" not in columns:
            columns_to_add.append(("reviewed_at", "DATETIME"))
        
        if not columns_to_add:
            print("✅ All review columns already exist. No migration needed.")
            return
        
        # Add the columns
        for col_name, col_def in columns_to_add:
            print(f"🔧 Adding {col_name} column to predictions table...")
            cursor.execute(f"ALTER TABLE predictions ADD COLUMN {col_name} {col_def}")
        
        conn.commit()
        print(f"✅ Successfully added {len(columns_to_add)} column(s)!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
