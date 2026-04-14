# RBI Circular Scrapper API Endpoints

This document outlines all available API endpoints for the project.

## Authentication
Endpoints for managing user accounts and sessions.

### Login
- **URL**: `/api/v1/auth/login`
- **Method**: `POST`
- **Body**: `username`, `password` (Form data)
- **Response**: JWT Access Token

### Register
- **URL**: `/api/v1/auth/register`
- **Method**: `POST`
- **Body**: `email`, `password`, `full_name`
- **Response**: User object

---

## API Key Management
Endpoints for admins to manage the secure access key for external projects (e.g., RAG systems).

### Rotate/Update API Key
- **URL**: `/api/v1/api-keys/`
- **Method**: `POST`
- **Auth**: Admin JWT required
- **Body**: `{"label": "string"}` (Optional)
- **Note**: This will deactivate the previous key and generate a new one. You can call this with an empty JSON `{}` for auto-generation.

### Get Active API Key
- **URL**: `/api/v1/api-keys/`
- **Method**: `GET`
- **Auth**: Admin JWT required
- **Response**: The currently active API key information.

### Revoke API Key
- **URL**: `/api/v1/api-keys/`
- **Method**: `DELETE`
- **Auth**: Admin JWT required
- **Note**: This will deactivate the current key without creating a new one.

---

## Scraper Management
Endpoints for triggering and monitoring the RBI scraping process.

### Trigger Sync
- **URL**: `/api/v1/scraper/sync`
- **Method**: `POST`
- **Auth**: Admin JWT required
- **Action**: Triggers scraping in the background.

---

## Data Access (Downloads)
Endpoints for external projects to fetch the scraped data. Secured by the API Key.

### List Files
- **URL**: `/api/v1/downloads/list`
- **Method**: `GET`
- **Auth**: `X-API-Key` header required
- **Response**: List of filenames in the `downloads` directory.

### Download File
- **URL**: `/api/v1/downloads/file/{filename}`
- **Method**: `GET`
- **Auth**: `X-API-Key` header required
- **Response**: The actual file content.
