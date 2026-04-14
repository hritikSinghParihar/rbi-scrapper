from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.circular import Circular
from app.services.circular_service import circular_service
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Circular])
def read_circulars(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Retrieve circulars."""
    circulars = circular_service.get_multi(db, skip=skip, limit=limit)
    return circulars

@router.get("/{id}", response_model=Circular)
def read_circular(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get circular by ID."""
    circular = db.query(Circular).filter(Circular.id == id).first()
    if not circular:
        raise HTTPException(status_code=404, detail="Circular not found")
    return circular
