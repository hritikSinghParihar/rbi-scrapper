import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
import os
import re
from datetime import datetime
import io

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv

from logger import get_logger

logger = get_logger(__name__)

# Load environment variables from .env
load_dotenv()

INDEX_URL = "https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx"

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
ROOT_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")

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
                logger.warning(f"OAuth credentials file not found: {SERVICE_ACCOUNT_FILE}. Google Drive upload will not work.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                SERVICE_ACCOUNT_FILE, SCOPES)
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
    return httpx.Client(
        headers={"User-Agent": "Mozilla/5.0"}, 
        timeout=30, 
        follow_redirects=True
    )

def sanitize_filename(name):
    """Removes invalid characters from a string to make it a safe Windows/Drive filename."""
    clean_name = re.sub(r'[\\/*?:"<>|]', '_', name)
    return clean_name.strip()

# Cache for folder IDs to minimize API calls
folder_cache = {}

def get_or_create_folder(folder_name, parent_id):
    """Gets a folder ID by name in a specific parent, creates it if it doesn't exist."""
    cache_key = f"{parent_id}/{folder_name}"
    if cache_key in folder_cache:
        return folder_cache[cache_key]

    if not drive_service:
        return None

    # Escape quotes in folder name just in case
    safe_folder_name = folder_name.replace("'", "\\'")
    query = f"name='{safe_folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])

    if files:
        folder_id = files[0].get('id')
    else:
        # Create it
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
        logger.info(f"Created folder '{folder_name}' with ID: {folder_id}")

    folder_cache[cache_key] = folder_id
    return folder_id

def file_exists_in_drive(filename, parent_id):
    """Checks if a file exists in the specific Google Drive folder."""
    if not drive_service:
        return False
        
    safe_filename = filename.replace("'", "\\'")
    query = f"name='{safe_filename}' and '{parent_id}' in parents and trashed=false"
    response = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])
    return len(files) > 0

def get_circular_links(client, year, month):
    logger.info(f"Loading main index page to capture tokens: {INDEX_URL}")
    r_get = client.get(INDEX_URL)
    
    if r_get.status_code != 200:
        logger.error(f"Failed to load index page. Status code: {r_get.status_code}")
        return []
        
    tree_get = HTMLParser(r_get.text)
    
    form_data = {}
    for input_tag in tree_get.css("input[type='hidden']"):
        name = input_tag.attributes.get("name")
        if name:
            form_data[name] = input_tag.attributes.get("value", "")
            
    form_data["hdnYear"] = str(year)
    form_data["hdnMonth"] = str(month)
    
    logger.info(f"Requesting data for Year: {year}, Month: {month}...")
    r_post = client.post(INDEX_URL, data=form_data)
    
    if r_post.status_code != 200:
        logger.error(f"Filtered results failed. Status code: {r_post.status_code}")
        return []
        
    tree = HTMLParser(r_post.text)
    
    links = {}
    for a in tree.css("a"):
        href = a.attributes.get("href", "")
        if "BS_CircularIndexDisplay.aspx?Id=" in href:
            full_url = urljoin(INDEX_URL, href)
            circular_num = a.text(strip=True)
            if not circular_num:
                circular_num = "Unknown_Circular_" + href.split("Id=")[-1]
            
            links[full_url] = {"url": full_url, "name": circular_num}
            
    return list(links.values())

def download_pdfs(client, links, year, month):
    if not links:
        logger.info(f"No circulars found for {year}-{month:02d}.")
        return

    if not drive_service or not ROOT_FOLDER_ID:
        logger.error("Drive service not initialized or DRIVE_FOLDER_ID is missing in .env. Skipping download.")
        return

    total = len(links)
    logger.info(f"Found {total} unique circulars for {year}-{month:02d}.")
    
    year_str = str(year)
    month_str = str(month).zfill(2)
    
    year_folder_id = get_or_create_folder(year_str, ROOT_FOLDER_ID)
    if not year_folder_id:
        logger.error(f"Could not create year folder {year_str}. Skipping.")
        return
        
    month_folder_id = get_or_create_folder(month_str, year_folder_id)
    if not month_folder_id:
        logger.error(f"Could not create month folder {month_str}. Skipping.")
        return
    
    for i, link_info in enumerate(links, start=1):
        url = link_info["url"]
        meaningful_name = sanitize_filename(link_info["name"])
        
        path_lower = f"{meaningful_name}.pdf"
        path_upper = f"{meaningful_name}.PDF"
        
        if file_exists_in_drive(path_lower, month_folder_id) or file_exists_in_drive(path_upper, month_folder_id):
            logger.info(f"[{i}/{total}] Already in Google Drive (SKIPPED FETCH): {meaningful_name}")
            continue
            
        logger.info(f"[{i}/{total}] Connecting to detail page: {url}")
        try:
            page = client.get(url)
            tree = HTMLParser(page.text)
            
            pdf_tag = tree.css_first('a[id^="APDF_"]')
            if not pdf_tag:
                logger.warning(f"[{i}/{total}] No PDF link found on this page. Skipping.")
                continue
                
            pdf_url = pdf_tag.attributes.get("href", "")
            
            ext = os.path.splitext(pdf_url)[1] 
            if not ext:
                ext = ".pdf"
                
            filename = f"{meaningful_name}{ext}"
            
            if file_exists_in_drive(filename, month_folder_id):
                logger.info(f"[{i}/{total}] Already in Google Drive: {filename}")
                continue
                
            logger.info(f"[{i}/{total}] Streaming to RAM & Uploading to Google Drive: {filename}")
            
            with client.stream("GET", pdf_url) as stream_response:
                pdf_bytes = io.BytesIO(stream_response.read())
                
                file_metadata = {
                    'name': filename,
                    'parents': [month_folder_id]
                }
                
                media = MediaIoBaseUpload(pdf_bytes, mimetype='application/pdf', resumable=True)
                
                drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                
            logger.info(f"[{i}/{total}] Successfully stored in Google Drive: {year_str}/{month_str}/{filename}")
            
        except Exception as e:
            logger.error(f"[{i}/{total}] Error processing {url}: {e}")

def run_scraper():
    logger.info("Starting RBI Scraper in Google Drive Mode...")
    current_year = datetime.now().year
    start_year = 2025
    
    with setup_client() as client:
        for year in range(start_year, current_year + 1):
            for month in range(1, 13):
                links = get_circular_links(client, year, month)
                download_pdfs(client, links, year, month)
                
    logger.info("RBI Google Drive Scraper finished successfully.")
