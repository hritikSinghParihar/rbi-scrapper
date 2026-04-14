import secrets
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKey as ApiKeySchema, ApiKeyCreate

router = APIRouter()

@router.post("/", response_model=ApiKeySchema)
def rotate_api_key(
    *,
    db: Session = Depends(deps.get_db),
    api_key_in: Optional[ApiKeyCreate] = Body(None),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generate or rotate the single API key."""
    # Deactivate all existing keys first
    db.query(ApiKey).filter(ApiKey.is_active == True).update({"is_active": False})
    
    # Generate a new secure 32-character random string
    new_key = secrets.token_urlsafe(32)
    
    label = api_key_in.label if api_key_in and api_key_in.label else "Main Access Key"
    
    api_key = ApiKey(
        key=new_key,
        label=label,
        owner_id=current_user.id
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

@router.get("/", response_model=Optional[ApiKeySchema])
def get_active_api_key(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get the currently active API key."""
    return db.query(ApiKey).filter(ApiKey.is_active == True).first()

@router.delete("/", response_model=ApiKeySchema)
def revoke_active_key(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Revoke the currently active API key."""
    api_key = db.query(ApiKey).filter(ApiKey.is_active == True).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="No active API Key found")
    
    api_key.is_active = False
    db.commit()
    db.refresh(api_key)
    return api_key
