import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.api_key import ApiKey
from app.models.user import User

def create_api_key(key, label, email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} not found.")
            return

        api_key = db.query(ApiKey).filter(ApiKey.key == key).first()
        if api_key:
            print(f"API Key {key} already exists.")
            api_key.is_active = True
        else:
            api_key = ApiKey(
                key=key,
                label=label,
                is_active=True,
                owner_id=user.id
            )
            db.add(api_key)
        db.commit()
        print(f"API Key {key} created/activated successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_api_key("test_api_key_123", "RAG PDF Integration", "scrapper@example.com")
