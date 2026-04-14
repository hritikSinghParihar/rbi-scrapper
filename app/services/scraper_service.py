from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.utils.logger import get_logger
from app.scraper.rbi_scraper import RBIScraper
from app.scraper.downloader import FileDownloader
from app.services.circular_service import circular_service
from app.schemas.circular import CircularCreate

logger = get_logger(__name__)

class ScraperService:
    def __init__(self):
        self.downloader = FileDownloader()

    def run_sync(self, db: Session, start_year: Optional[int] = None):
        logger.info("Starting RBI Scraper Sync...")
        current_year = datetime.now().year
        year_to_start = start_year or settings.START_YEAR
        
        with RBIScraper() as scraper:
            for year in range(year_to_start, current_year + 1):
                for month in range(1, 13):
                    if year == current_year and month > datetime.now().month:
                        break
                        
                    links = scraper.get_links(year, month)
                    if not links: continue
                    
                    # Setup Drive Group if possible
                    drive_month_id = None
                    if self.downloader.drive_service and settings.DRIVE_FOLDER_ID:
                        y_id = self.downloader.get_or_create_drive_folder(str(year), settings.DRIVE_FOLDER_ID)
                        if y_id:
                            drive_month_id = self.downloader.get_or_create_drive_folder(str(month).zfill(2), y_id)

                    for link_info in links:
                        url = link_info["url"]
                        name = self.downloader.sanitize_filename(link_info["name"])
                        filename = f"{name}.pdf"
                        
                        # Check DB first
                        existing = circular_service.get_circular_by_url(db, url)
                        if existing:
                            logger.info(f"Skipping (already in DB): {name}")
                            continue

                        # Download PDF
                        content = scraper.download_pdf(url)
                        if not content:
                            logger.warning(f"Failed to download PDF: {name}")
                            continue
                        
                        # Save Locally
                        local_path = self.downloader.save_locally(content, year, month, filename)
                        
                        # Upload to Drive
                        drive_id = None
                        if drive_month_id:
                            drive_id = self.downloader.upload_to_drive(content, filename, drive_month_id)
                        
                        # Save to DB
                        circular_in = CircularCreate(
                            title=link_info["name"],
                            url=url,
                            publication_date=datetime(year, month, 1), # Simplified, should parse from HTML in future
                            year=year,
                            month=month
                        )
                        circular_service.create_circular(db, circular_in, local_path, drive_id)
                        logger.info(f"Saved to DB and Storage: {name}")

        logger.info("RBI Scraper Sync task completed.")

scraper_service = ScraperService()
