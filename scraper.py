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

from logger import get_logger

logger = get_logger(__name__)

# Base directory for downloads
DOWNLOAD_DIR = Path("downloads")
INDEX_URL = "https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx"

def setup_client():
    return requests.Session(
        impersonate="chrome120",
        timeout=30, 
    )

def sanitize_filename(name):
    """Removes invalid characters from a string to make it a safe Windows filename."""
    clean_name = re.sub(r'[\\/*?:"<>|]', '_', name)
    return clean_name.strip()

def file_exists_locally(year, month, filename):
    """Checks if a file exists in the local download directory."""
    file_path = DOWNLOAD_DIR / str(year) / f"{month:02d}" / filename
    return file_path.exists()

def get_circular_links(client, year, month):
    # Establish a "human-like" session by hitting the homepage first
    try:
        if not client.cookies:
            logger.info("Accessing homepage to establish session cookies...")
            resp = client.get("https://www.rbi.org.in/")
            logger.info(f"Homepage status: {resp.status_code}")
            time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        logger.warning(f"Failed to load homepage for cookies: {e}")

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
        
        # FAST SKIP LOGIC for Local Storage
        if file_exists_locally(year, month, f"{meaningful_name}.pdf") or \
           file_exists_locally(year, month, f"{meaningful_name}.PDF"):
            logger.info(f"[{i}/{total}] Already local (SKIPPED FETCH): {meaningful_name}")
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
            
            # Check one last time just in case
            if file_exists_locally(year, month, filename):
                logger.info(f"[{i}/{total}] Already local: {filename}")
                continue
                
            logger.info(f"[{i}/{total}] Saving to local disk: {filename}")
            
            # Efficiently transfer from RBI Servers -> RAM -> Local File
            stream_response = client.get(pdf_url)
            if stream_response.status_code == 200:
                content = stream_response.content
                if not content:
                    logger.error(f"[{i}/{total}] Downloaded content is EMPTY for {filename}")
                    continue
                    
                # Ensure directory exists
                dest_dir = DOWNLOAD_DIR / str(year) / f"{month:02d}"
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                # Write content to local file
                with open(dest_dir / filename, "wb") as f:
                    f.write(content)
                    
                logger.info(f"[{i}/{total}] Successfully stored locally: {filename}")
            else:
                logger.error(f"[{i}/{total}] Failed to download PDF. Status: {stream_response.status_code}")
            
        except Exception as e:
            logger.error(f"[{i}/{total}] Error processing {url}: {e}")

def run_scraper():
    logger.info("Starting RBI Scraper in Local Storage Mode...")
    current_year = datetime.now().year
    start_year = 2025  # Starting at 2025 as requested
    
    with setup_client() as client:
        for year in range(start_year, current_year + 1):
            for month in range(1, 13):
                links = get_circular_links(client, year, month)
                download_pdfs(client, links, year, month)
                # Random delay between months to avoid bot detection
                time.sleep(random.uniform(2.0, 5.0))
                
    logger.info("RBI Cloud Scraper finished successfully.")
