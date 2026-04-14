import time
import random
from curl_cffi import requests
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.core.constants import INDEX_URL, HOME_URL, CHROME_IMPERSONATION
from app.utils.logger import get_logger
from app.scraper.parser import parse_hidden_form_data, parse_circular_links, parse_pdf_link

logger = get_logger(__name__)

class RBIScraper:
    def __init__(self):
        self.session = self._setup_session()

    def _setup_session(self) -> requests.Session:
        return requests.Session(
            impersonate=CHROME_IMPERSONATION,
            timeout=30, 
        )

    def ensure_session(self):
        """Hits homepage to establish cookies if not present."""
        if not self.session.cookies:
            try:
                logger.info("Establishing session cookies...")
                resp = self.session.get(HOME_URL)
                logger.info(f"Homepage status: {resp.status_code}")
                time.sleep(random.uniform(1.0, 3.0))
            except Exception as e:
                logger.warning(f"Failed to load homepage: {e}")

    def get_links(self, year: int, month: int) -> List[Dict[str, str]]:
        self.ensure_session()
        
        logger.info(f"Fetching index for {year}-{month:02d}")
        r_get = self.session.get(INDEX_URL)
        if r_get.status_code != 200:
            logger.error(f"Failed to load index. Status: {r_get.status_code}")
            return []
            
        form_data = parse_hidden_form_data(r_get.text)
        form_data["hdnYear"] = str(year)
        form_data["hdnMonth"] = str(month)
        
        r_post = self.session.post(INDEX_URL, data=form_data)
        if r_post.status_code != 200:
            logger.error(f"Failed to post form. Status: {r_post.status_code}")
            return []
            
        return parse_circular_links(r_post.text)

    def download_pdf(self, url: str) -> Optional[bytes]:
        try:
            page = self.session.get(url)
            if page.status_code != 200:
                return None
                
            pdf_url = parse_pdf_link(page.text, url)
            if not pdf_url:
                return None

            resp = self.session.get(pdf_url)
            if resp.status_code == 200 and resp.content:
                return resp.content
            return None
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
            return None

    def close(self):
        self.session.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
