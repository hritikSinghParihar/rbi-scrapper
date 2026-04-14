from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ApiKeyBase(BaseModel):
    label: str = "Main Access Key"

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyUpdate(ApiKeyBase):
    is_active: Optional[bool] = None

class ApiKey(ApiKeyBase):
    id: int
    key: str
    is_active: bool
    created_at: datetime
    owner_id: int

    class Config:
        from_attributes = True
