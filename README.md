# RBI Circular Scraper (Dual Storage)

A robust automated scraper for RBI (Reserve Bank of India) circulars. This tool downloads PDFs from the RBI website, saves them locally, and pushes them to a specified Google Drive folder.

## Features

- **Dual Storage**: Saves files locally in `rbi_pdfs/{year}/{month}/` and uploads them to Google Drive.
- **Bot Avoidance**: Uses `curl_cffi` with Chrome impersonation and random delays to minimize the risk of being blocked by the RBI server.
- **Incremental Scraping**: Checks for existing files (locally and on Drive) before downloading to save bandwidth and time.
- **PDF Fix**: Includes a session establishment phase to ensure reliable PDF link capturing and downloads.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Drive Integration**:
   - Obtain a `credentials.json` file from the Google Cloud Console (OAuth 2.0 Client ID).
   - Place `credentials.json` in the root directory.
   - On the first run, the script will open a browser for authentication and save a `token.json` file.

3. **Environment Variables**:
   Create a `.env` file or set the following variables:
   - `DRIVE_FOLDER_ID`: The ID of the Google Drive folder where you want to store the circulars.
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your `credentials.json` (defaults to `credentials.json`).

## Usage

Simply run the main script:
```bash
python main.py
```

The script is configured to scrape from **2025 onwards**. You can adjust the `start_year` in `scraper.py` if needed.

## Directory Structure
- `rbi_pdfs/`: Local storage for downloaded circulars.
- `logs/`: Application logs.
- `scraper.py`: Core logic for scraping and uploading.
- `main.py`: Entry point for the application.
- `logger.py`: Logging configuration.

## Safety Note
The script ignores `credentials.json`, `token.json`, and the `rbi_pdfs/` directory via `.gitignore` to prevent sensitive data or large binary files from being committed to your repository.
