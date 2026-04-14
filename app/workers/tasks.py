from app.workers.celery_worker import celery_app
from app.services.scraper_service import scraper_service
from app.db.session import SessionLocal
from app.utils.logger import get_logger

logger = get_logger(__name__)

@celery_app.task(name="app.workers.tasks.run_scraper_task")
def run_scraper_task(start_year: int = None):
    logger.info("Celery task: Starting RBI Scraper Sync")
    db = SessionLocal()
    try:
        scraper_service.run_sync(db, start_year=start_year)
    finally:
        db.close()
    logger.info("Celery task: RBI Scraper Sync completed")
