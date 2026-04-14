from typing import Any
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.api import deps
from app.services.scraper_service import scraper_service
from app.models.user import User

router = APIRouter()

@router.post("/sync")
def trigger_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Trigger a manual scraper sync."""
    # Note: In a full prod app, we'd use Celery here. 
    # For now, using FastAPI BackgroundTasks as a fallback if Celery isn't running.
    background_tasks.add_task(scraper_service.run_sync, db)
    return {"message": "Scraper sync triggered in background"}

@router.post("/celery-sync")
def trigger_celery_sync(
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Trigger a scraper sync using Celery."""
    from app.workers.tasks import run_scraper_task
    task = run_scraper_task.delay()
    return {"task_id": task.id, "status": "Pending"}
