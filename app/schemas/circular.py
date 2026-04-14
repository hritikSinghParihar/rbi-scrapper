from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class CircularBase(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    publication_date: Optional[datetime] = None
    year: Optional[int] = None
    month: Optional[int] = None

class CircularCreate(CircularBase):
    title: str
    url: str
    publication_date: datetime
    year: int
    month: int

class CircularUpdate(CircularBase):
    pass

class CircularInDBBase(CircularBase):
    id: int
    local_path: Optional[str] = None
    drive_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Circular(CircularInDBBase):
    pass
