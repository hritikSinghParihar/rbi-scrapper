import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import engine, SessionLocal, Base
from app.models.user import User
from app.services.auth_service import auth_service
from app.services.scraper_service import scraper_service
from app.schemas.user import UserCreate
from app.utils.logger import get_logger

logger = get_logger(__name__)

def setup_and_run():
    logger.info("Starting Full System Setup...")
    
    # 1. Initialize Database
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Check if admin exists, if not create
        admin_email = "admin@example.com"
        admin_pass = "admin123"
        
        user = auth_service.get_user_by_email(db, admin_email)
        if not user:
            logger.info(f"Creating default admin user: {admin_email}")
            user_in = UserCreate(
                email=admin_email,
                password=admin_pass,
                full_name="System Admin"
            )
            auth_service.create_user(db, user_in)
            logger.info("Admin user created successfully.")
        else:
            logger.info("Admin user already exists.")
            
        # 3. Trigger Scraper Sync (Full Process)
        # We'll just run for Jan 2025 to keep the test short and verify success
        logger.info("Starting Scraper Sync (Simulation of API trigger)...")
        scraper_service.run_sync(db, start_year=2025)
        
        logger.info("Full system process completed successfully.")
        logger.info(f"You can now login to the API with: {admin_email} / {admin_pass}")

    except Exception as e:
        logger.error(f"Error during system setup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    setup_and_run()
