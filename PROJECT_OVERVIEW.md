# Documentation - RBI Circular Scraper

This is an automated Python-based tool designed to incrementally fetch and store official circulars from the Reserve Bank of India (RBI) website.

## 🛠️ Project Details
- **Language**: Python 3.13+
- **HTTP Engine**: `curl_cffi` (used specifically for bypassing bot-detection filters).
- **Storage Strategy**: Local filesystem storage (with year/month organization).

## 📂 Folder Structure
```text
rbi-scrapper/
├── downloads/        # Stored PDFs (created automatically)
│   └── 2025/         # Organized by Year
│       └── 01/       # Organized by Month
├── logs/             # Scraper execution logs
├── main.py           # Entry point (Run this file)
├── scraper.py        # Core logic (Scraping, Fetching, Saving)
├── logger.py         # Logging configuration
└── requirements.txt  # Python dependencies
```

## 🚀 Functionalities
1.  **Bot Bypass**: Automatically mimics a real Chrome browser's TLS signature to avoid being blocked by the RBI firewall (Status 418).
2.  **Session Establishment**: Hits the RBI homepage first to get valid security cookies before attempting to scrape data.
3.  **ASP.NET Form Handling**: Automatically parses hidden tokens (`__VIEWSTATE`, etc.) from the RBI site to correctly filter by Year and Month.
4.  **Incremental Fast-Skip**: Checks if a PDF already exists on your hard drive before downloading. If it's there, it skips it to save time and bandwidth.
5.  **Clean Renaming**: Renames the random hash-names used by RBI into legible, meaningful filenames based on the circular's title.

## 📈 Current Status
- **Verified**: The script successfully connects to RBI, parses the circular list, and downloads full-content PDFs (non-zero size) into the `downloads/` folder.
