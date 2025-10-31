"""
Script to create a super admin user
Usage: python create_super_admin.py
"""
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.database import SessionLocal, User, create_tables
from app.utils.auth import get_password_hash

def create_super_admin():
    """Create super admin user"""
    
    # Ensure tables exist
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Check if super admin already exists
        existing = db.query(User).filter(User.email == "super@gmail.com").first()
        
        if existing:
            print("Super admin user already exists!")
            print(f"Email: {existing.email}")
            print(f"Role: {existing.role}")
            return
        
        # Create super admin
        super_admin = User(
            email="super@gmail.com",
            full_name="Super Administrator",
            organization="ODOMOS System",
            hashed_password=get_password_hash("pw"),
            role="super_admin",
            is_active=True
        )
        
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        
        print("✅ Super admin user created successfully!")
        print(f"Email: super@gmail.com")
        print(f"Password: pw")
        print(f"Role: super_admin")
        print(f"Full Name: {super_admin.full_name}")
        print(f"Organization: {super_admin.organization}")
        
    except Exception as e:
        print(f"❌ Error creating super admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()
