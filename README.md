# RBI Circular Cloud Scraper

An advanced, asynchronous-ready Python web scraper designed to bypass ASP.NET forms on the Reserve Bank of India (RBI) website, incrementally fetch circulars and efficiently push them directly into Cloudflare R2 storage without writing files locally.

## Features

- **ASP.NET PostBack Simulation**: Natively parses `__VIEWSTATE` hidden variables from the `aspx` DOM to correctly simulate javascript-heavy filter forms (Year and Month) passively.
- **In-Memory Streaming (Zero-Disk)**: Protects server disk space by streaming downloaded PDFs from `httpx` straight into an `io.BytesIO` byte-buffer which is then instantly uploaded to Cloudflare R2.
- **Incremental Fast-Skip Cache**: Never wastes time downloading the same circular twice. Operates `boto3.head_object` evaluations against the bucket to assert existence prior to committing bandwidth arrays.
- **Meaningful Sanitization**: Strips invalid Windows characters and resolves PDF names from their default RBI-hashes (`06NT29AAEE6D...`) to hyper-legible dates.

## Dependencies
- `httpx` - Fast HTTP fetching
- `selectolax` - Hyper-fast HTML parsing (C-bindings)
- `boto3` - S3/Cloudflare R2 interfacing
- `python-dotenv` - Secure credential loading

```bash
pip install httpx selectolax boto3 python-dotenv
```

## Security & Setup

Create a `.env` file in the root directory mirroring your Cloudflare R2 S3-compatability API configuration:

```env
R2_ENDPOINT_URL=https://<YOUR_ACCOUNT_ID>.r2.cloudflarestorage.com
R2_BUCKET_NAME=rbi-circulars
R2_ACCESS_KEY_ID=YOUR_R2_ACCESS_KEY_HERE
R2_SECRET_ACCESS_KEY=YOUR_R2_SECRET_KEY_HERE
```

## Usage

Simply initialize the scraper payload through the main entry point:

```bash
python main.py
```

It will sequence across all months starting from 2025 up to the current year, populate your cloud storage, and output iteration-level tracking data to the `/logs` directory.
