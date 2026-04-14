# RBI Circular Scrapper (Production Grade)

A robust, scalable scraper for RBI circulars using FastAPI, SQLAlchemy, and Celery.

## Features
- **FastAPI API**: Manage users, list circulars, and trigger syncs.
- **Asynchronous Scraping**: Powered by Celery and Redis.
- **Dual Storage**: Local filesystem and Google Drive integration.
- **Database Tracking**: All circulars are tracked in a database to prevent duplicates.
- **Dockerized**: Easy deployment with Docker Compose.

## Directory Structure
- `app/`: Main application package
  - `api/`: FastAPI routes
  - `core/`: Configuration and security
  - `db/`: Database models and session
  - `scraper/`: Refactored scraping logic
  - `services/`: Business logic
  - `workers/`: Celery tasks
- `downloads/`: Local storage for PDFs
- `scripts/`: Initialization and maintenance scripts
- `tests/`: Testing suite

## Getting Started

### 1. Prerequisites
- Docker and Docker Compose
- `credentials.json` for Google Drive (if needed)

### 2. Setup environment
Create a `.env` file from the template:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:password@db:5432/rbi_scrapper
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
DRIVE_FOLDER_ID=your-google-drive-folder-id
```

### 3. Run with Docker
```bash
docker-compose up -d --build
```

### 4. Initialize Database
```bash
docker-compose exec api python scripts/init_db.py
```

### 5. Access API
Visit `http://localhost:8000/docs` for the interactive API documentation.

## Running Locally (without Docker)
1. Install dependencies: `pip install -r requirements.txt`
2. Start Redis (required for Celery)
3. Run API: `uvicorn app.main:app --reload`
4. Run Worker: `celery -A app.workers.celery_worker.celery_app worker --loglevel=info`
