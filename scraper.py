import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
import os
import re
from datetime import datetime
import io

import boto3
import botocore
from botocore.config import Config
from dotenv import load_dotenv

from logger import get_logger

logger = get_logger(__name__)

# Load environment variables from .env
load_dotenv()

INDEX_URL = "https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx"
R2_BUCKET = os.environ.get("R2_BUCKET_NAME", "rbi-circulars")

# Initialize Cloudflare R2 Client
r2_client = boto3.client(
    's3',
    endpoint_url=os.environ.get("R2_ENDPOINT_URL"),
    aws_access_key_id=os.environ.get("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("R2_SECRET_ACCESS_KEY"),
    region_name='auto',
    config=Config(signature_version='s3v4')
)

def setup_client():
    return httpx.Client(
        headers={"User-Agent": "Mozilla/5.0"}, 
        timeout=30, 
        follow_redirects=True
    )

def sanitize_filename(name):
    """Removes invalid characters from a string to make it a safe Windows filename."""
    clean_name = re.sub(r'[\\/*?:"<>|]', '_', name)
    return clean_name.strip()

def file_exists_in_r2(key):
    """Checks if a file exists in the R2 bucket without downloading it."""
    try:
        r2_client.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        raise

def get_circular_links(client, year, month):
    logger.info(f"Loading main index page to capture tokens: {INDEX_URL}")
    r_get = client.get(INDEX_URL)
    
    if r_get.status_code != 200:
        logger.error(f"Failed to load index page. Status code: {r_get.status_code}")
        return []
        
    tree_get = HTMLParser(r_get.text)
    
    # ASP.NET requires sending back its hidden state fields
    form_data = {}
    for input_tag in tree_get.css("input[type='hidden']"):
        name = input_tag.attributes.get("name")
        if name:
            form_data[name] = input_tag.attributes.get("value", "")
            
    # Set the hidden filters for Year and Month
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
            # Use the circular text directly as the meaningful name
            circular_num = a.text(strip=True)
            if not circular_num:
                circular_num = "Unknown_Circular_" + href.split("Id=")[-1]
            
            links[full_url] = {"url": full_url, "name": circular_num}
            
    return list(links.values())

def download_pdfs(client, links, year, month):
    if not links:
        logger.info(f"No circulars found for {year}-{month:02d}.")
        return

    total = len(links)
    logger.info(f"Found {total} unique circulars for {year}-{month:02d}.")
    
    for i, link_info in enumerate(links, start=1):
        url = link_info["url"]
        meaningful_name = sanitize_filename(link_info["name"])
        
        # FAST SKIP LOGIC for Cloudflare R2
        cloud_base_path = f"{year}/{str(month).zfill(2)}/{meaningful_name}"
        path_lower = f"{cloud_base_path}.pdf"
        path_upper = f"{cloud_base_path}.PDF"
        
        if file_exists_in_r2(path_lower) or file_exists_in_r2(path_upper):
            logger.info(f"[{i}/{total}] Already in R2 (SKIPPED FETCH): {meaningful_name}")
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
            
            # Keep the original extension (.PDF or .pdf)
            ext = os.path.splitext(pdf_url)[1] 
            if not ext:
                ext = ".pdf"
                
            filename = f"{meaningful_name}{ext}"
            cloud_filepath = f"{year}/{str(month).zfill(2)}/{filename}"
            
            # Check one last time just in case of an exotic extension
            if file_exists_in_r2(cloud_filepath):
                logger.info(f"[{i}/{total}] Already in R2: {filename}")
                continue
                
            logger.info(f"[{i}/{total}] Streaming to RAM & Uploading to R2: {filename}")
            
            # Efficiently transfer from RBI Servers -> RAM -> Cloudflare R2
            with client.stream("GET", pdf_url) as stream_response:
                # Load the few-megabyte PDF chunk into memory buffer
                pdf_bytes = io.BytesIO(stream_response.read())
                
                # Upload the buffer to your bucket
                r2_client.upload_fileobj(pdf_bytes, R2_BUCKET, cloud_filepath)
                
            logger.info(f"[{i}/{total}] Successfully stored in R2: {cloud_filepath}")
            
        except Exception as e:
            logger.error(f"[{i}/{total}] Error processing {url}: {e}")

def run_scraper():
    logger.info("Starting RBI Scraper in Cloudflare R2 Mode...")
    current_year = datetime.now().year
    start_year = 2025  # Starting at 2025 as requested
    
    with setup_client() as client:
        for year in range(start_year, current_year + 1):
            for month in range(1, 13):
                links = get_circular_links(client, year, month)
                download_pdfs(client, links, year, month)
                
    logger.info("RBI Cloud Scraper finished successfully.")
