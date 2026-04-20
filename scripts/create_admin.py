import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin():
    db: Session = SessionLocal()
    
    # Check if admin already exists
    admin_email = "admin@wisipay.com"
    existing_user = db.query(User).filter(User.email == admin_email).first()
    
    if existing_user:
        print(f"User {admin_email} already exists.")
        return

    admin_user = User(
        email=admin_email,
        hashed_password=get_password_hash("admin123"),
        full_name="System Admin",
        is_superuser=True,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    print(f"Admin user created successfully: {admin_email}")

if __name__ == "__main__":
    create_admin()
