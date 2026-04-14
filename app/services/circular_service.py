from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.circular import Circular
from app.schemas.circular import CircularCreate, CircularUpdate

class CircularService:
    def get_circular_by_url(self, db: Session, url: str) -> Optional[Circular]:
        return db.query(Circular).filter(Circular.url == url).first()

    def create_circular(self, db: Session, circular_in: CircularCreate, local_path: str, drive_id: Optional[str] = None) -> Circular:
        db_circular = Circular(
            **circular_in.model_dump(),
            local_path=local_path,
            drive_id=drive_id
        )
        db.add(db_circular)
        db.commit()
        db.refresh(db_circular)
        return db_circular

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Circular]:
        return db.query(Circular).offset(skip).limit(limit).all()

circular_service = CircularService()
