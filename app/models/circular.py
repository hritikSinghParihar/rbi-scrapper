from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db.session import Base

class Circular(Base):
    __tablename__ = "circulars"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    publication_date = Column(DateTime, index=True)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    local_path = Column(String)
    drive_id = Column(String, nullable=True)
    content_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
