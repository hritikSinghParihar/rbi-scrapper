import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.scraper.rbi_scraper import RBIScraper
from app.utils.logger import get_logger

logger = get_logger(__name__)

def test_scraping():
    logger.info("Testing RBI Scraper logic...")
    year = 2025
    month = 1
    
    try:
        with RBIScraper() as scraper:
            logger.info(f"Attempting to fetch links for {year}-{month:02d}...")
            links = scraper.get_links(year, month)
            
            if not links:
                logger.error("No links found!")
                return
            
            logger.info(f"Found {len(links)} links.")
            for i, link in enumerate(links[:3]): # Show first 3
                logger.info(f"Link {i+1}: {link['name']} -> {link['url']}")
            
            # Test download of the first link
            test_url = links[0]['url']
            logger.info(f"Attempting to download first link: {test_url}")
            content = scraper.download_pdf(test_url)
            
            if content:
                logger.info(f"Successfully downloaded PDF. Size: {len(content)} bytes")
            else:
                logger.error("Failed to download PDF.")
                
    except Exception as e:
        logger.error(f"An error occurred during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraping()
