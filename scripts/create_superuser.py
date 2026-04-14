import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_superuser(email, password, full_name):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"User {email} already exists. Updating to superuser.")
            user.is_superuser = True
            user.hashed_password = get_password_hash(password)
        else:
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                is_superuser=True,
                is_active=True
            )
            db.add(user)
        db.commit()
        print(f"Superuser {email} created/updated successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/create_superuser.py <email> <password> [full_name]")
    else:
        email = sys.argv[1]
        password = sys.argv[2]
        full_name = sys.argv[3] if len(sys.argv) > 3 else "Admin User"
        create_superuser(email, password, full_name)
