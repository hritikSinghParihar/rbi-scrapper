from curl_cffi import requests
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
import os
import re
import time
import random
from datetime import datetime
import io
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv

from logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Constants
INDEX_URL = "https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx"
DOWNLOAD_DIR = Path("rbi_pdfs")
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
ROOT_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")

# Google Drive Initialization
def get_drive_service():
    creds = None
    token_file = 'token.json'
    
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                logger.warning(f"OAuth credentials file not found: {SERVICE_ACCOUNT_FILE}. Google Drive upload will be disabled.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(SERVICE_ACCOUNT_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

try:
    drive_service = get_drive_service()
except Exception as e:
    logger.error(f"Failed to initialize Google Drive service: {e}")
    drive_service = None

def setup_client():
    """Sets up a session with Chrome impersonation to avoid bot detection."""
    return requests.Session(
        impersonate="chrome120",
        timeout=30, 
    )

def sanitize_filename(name):
    """Removes invalid characters from a string to make it a safe Windows/Drive filename."""
    clean_name = re.sub(r'[\\/*?:"<>|]', '_', name)
    return clean_name.strip()

# Cache for folder IDs to minimize API calls
folder_cache = {}

def get_or_create_drive_folder(folder_name, parent_id):
    """Gets a folder ID by name in a specific parent, creates it if it doesn't exist."""
    cache_key = f"{parent_id}/{folder_name}"
    if cache_key in folder_cache:
        return folder_cache[cache_key]

    if not drive_service:
        return None

    safe_folder_name = folder_name.replace("'", "\\'")
    query = f"name='{safe_folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])

    if files:
        folder_id = files[0].get('id')
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
        logger.info(f"Created Drive folder '{folder_name}' with ID: {folder_id}")

    folder_cache[cache_key] = folder_id
    return folder_id

def file_exists_in_drive(base_filename, parent_id):
    """Checks if a file exists in Drive by searching for both .pdf and .PDF variants."""
    if not drive_service:
        return False
    
    # Drive API name search is case-sensitive, so we check for both common variants
    name = base_filename.rsplit('.', 1)[0]
    safe_name = name.replace("'", "\\'")
    
    # Query for both .pdf and .PDF extensions
    query = (f"(name='{safe_name}.pdf' or name='{safe_name}.PDF') "
             f"and '{parent_id}' in parents and trashed=false")
    
    response = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    existing_files = response.get('files', [])
    
    if existing_files:
        # Log if we found a match (helps debugging)
        found_name = existing_files[0].get('name')
        logger.debug(f"Found existing file in Drive: {found_name}")
        return True
        
    return False

def file_exists_locally(year, month, filename):
    """Checks if a file exists in the local download directory."""
    file_path = DOWNLOAD_DIR / str(year) / f"{month:02d}" / filename
    return file_path.exists()

def get_circular_links(client, year, month):
    """Fetches circular links for a specific year and month."""
    # PDF Fix from develop: establish a session by hitting homepage first
    try:
        if not client.cookies:
            logger.info("Accessing homepage to establish session...")
            client.get("https://www.rbi.org.in/")
            time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        logger.warning(f"Homepage access failed: {e}")

    logger.info(f"Loading index page: {INDEX_URL}")
    r_get = client.get(INDEX_URL)
    if r_get.status_code != 200:
        logger.error(f"Failed to load index page. Status: {r_get.status_code}")
        return []
        
    tree_get = HTMLParser(r_get.text)
    form_data = {tag.attributes.get("name"): tag.attributes.get("value", "") 
                 for tag in tree_get.css("input[type='hidden']") if tag.attributes.get("name")}
    
    form_data["hdnYear"] = str(year)
    form_data["hdnMonth"] = str(month)
    
    logger.info(f"Requesting Year: {year}, Month: {month}...")
    r_post = client.post(INDEX_URL, data=form_data)
    if r_post.status_code != 200:
        return []
        
    tree = HTMLParser(r_post.text)
    links = {}
    for a in tree.css("a"):
        href = a.attributes.get("href", "")
        if "BS_CircularIndexDisplay.aspx?Id=" in href:
            full_url = urljoin(INDEX_URL, href)
            name = a.text(strip=True) or ("Circular_" + href.split("Id=")[-1])
            links[full_url] = {"url": full_url, "name": name}
            
    return list(links.values())

def download_and_upload_pdf(client, link_info, year, month, drive_folder_id):
    """
    Downloads a PDF locally and then uploads it to Google Drive.
    Flow: Check Local -> Download if missing -> Check Drive -> Upload if missing.
    """
    url = link_info["url"]
    name = sanitize_filename(link_info["name"])
    filename = f"{name}.pdf"
    
    # 1. LOCAL CHECK & DOWNLOAD
    is_local = file_exists_locally(year, month, filename) or file_exists_locally(year, month, f"{name}.PDF")
    
    if not is_local:
        try:
            logger.info(f"Local file missing. Fetching detail page: {url}")
            page = client.get(url)
            tree = HTMLParser(page.text)
            pdf_tag = tree.css_first('a[id^="APDF_"]')
            if not pdf_tag:
                logger.warning(f"No PDF link found on page: {url}")
                return

            pdf_url = pdf_tag.attributes.get("href", "")
            resp = client.get(pdf_url)
            if resp.status_code == 200 and resp.content:
                # Save Locally
                dest_dir = DOWNLOAD_DIR / str(year) / f"{month:02d}"
                dest_dir.mkdir(parents=True, exist_ok=True)
                local_path = dest_dir / filename
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Downloaded and saved locally: {filename}")
                is_local = True # Mark as local for the next step
            else:
                logger.error(f"Failed to download PDF: {filename} (Status: {resp.status_code})")
                return # Can't upload if download failed
        except Exception as e:
            logger.error(f"Error during download of {filename}: {e}")
            return
    else:
        logger.info(f"Already exists locally: {filename}")

    # 2. DRIVE CHECK & UPLOAD
    if drive_folder_id:
        try:
            if not file_exists_in_drive(filename, drive_folder_id):
                logger.info(f"Uploading to Google Drive: {filename}")
                
                # Use the local file we just ensured exists
                local_path = DOWNLOAD_DIR / str(year) / f"{month:02d}" / filename
                if not local_path.exists(): local_path = local_path.with_suffix('.PDF')
                
                with open(local_path, "rb") as f:
                    media = MediaIoBaseUpload(io.BytesIO(f.read()), mimetype='application/pdf')
                    drive_service.files().create(
                        body={'name': filename, 'parents': [drive_folder_id]}, 
                        media_body=media
                    ).execute()
                logger.info(f"Successfully uploaded to Drive: {filename}")
            else:
                logger.info(f"Already exists in Google Drive: {filename}")
        except Exception as e:
            logger.error(f"Error during Drive upload of {filename}: {e}")

def run_scraper():
    logger.info("Starting RBI Scraper in DUAL STORAGE mode (Local + Google Drive)...")
    current_year = datetime.now().year
    start_year = 2025
    
    with setup_client() as client:
        for year in range(start_year, current_year + 1):
            for month in range(1, 13):
                links = get_circular_links(client, year, month)
                if not links: continue
                
                # Setup Drive Folders if needed
                month_drive_id = None
                if drive_service and ROOT_FOLDER_ID:
                    y_id = get_or_create_drive_folder(str(year), ROOT_FOLDER_ID)
                    if y_id: month_drive_id = get_or_create_drive_folder(str(month).zfill(2), y_id)

                for link in links:
                    download_and_upload_pdf(client, link, year, month, month_drive_id)
                
                # Bot detection delay
                time.sleep(random.uniform(2.0, 5.0))
                
    logger.info("RBI Scraper task completed.")
