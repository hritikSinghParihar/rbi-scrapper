import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "RBI Circular Scrapper"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-for-jwt-change-it")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "your-rag-project-api-secret-change-it")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    
    # RBI Scraper
    INDEX_URL: str = "https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx"
    DOWNLOAD_DIR: str = "downloads"
    START_YEAR: int = 2025
    
    # Google Drive
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    DRIVE_FOLDER_ID: Optional[str] = os.getenv("DRIVE_FOLDER_ID")
    SCOPES: List[str] = ['https://www.googleapis.com/auth/drive']
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
