import io
import os
import re
from pathlib import Path
from typing import Optional, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class FileDownloader:
    def __init__(self):
        self.download_dir = Path(settings.DOWNLOAD_DIR)
        self.drive_service = self._init_drive_service()
        self.folder_cache = {}

    def _init_drive_service(self) -> Optional[Any]:
        if not settings.GOOGLE_APPLICATION_CREDENTIALS or not os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
            logger.warning("Google Drive credentials not found. Drive upload disabled.")
            return None
        
        creds = None
        token_file = 'token.json'
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, settings.SCOPES)
            
        try:
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(settings.GOOGLE_APPLICATION_CREDENTIALS, settings.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
        except Exception as e:
            logger.error(f"Google Drive authentication failed: {e}")
            return None
        
        try:
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}")
            return None

    def sanitize_filename(self, name: str) -> str:
        clean_name = re.sub(r'[\\/*?:"<>|]', '_', name)
        return clean_name.strip()

    def get_or_create_drive_folder(self, folder_name: str, parent_id: str) -> Optional[str]:
        if not self.drive_service: return None
        
        cache_key = f"{parent_id}/{folder_name}"
        if cache_key in self.folder_cache:
            return self.folder_cache[cache_key]

        safe_folder_name = folder_name.replace("'", "\\'")
        query = f"name='{safe_folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        response = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = response.get('files', [])

        if files:
            folder_id = files[0].get('id')
        else:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            logger.info(f"Created Drive folder '{folder_name}' with ID: {folder_id}")

        self.folder_cache[cache_key] = folder_id
        return folder_id

    def file_exists_locally(self, year: int, month: int, filename: str) -> bool:
        file_path = self.download_dir / str(year) / f"{month:02d}" / filename
        return file_path.exists()

    def save_locally(self, content: bytes, year: int, month: int, filename: str) -> str:
        dest_dir = self.download_dir / str(year) / f"{month:02d}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        local_path = dest_dir / filename
        with open(local_path, "wb") as f:
            f.write(content)
        return str(local_path)

    def upload_to_drive(self, content: bytes, filename: str, folder_id: str) -> Optional[str]:
        if not self.drive_service: return None
        
        try:
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype='application/pdf')
            file = self.drive_service.files().create(
                body={'name': filename, 'parents': [folder_id]}, 
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')
        except Exception as e:
            logger.error(f"Error uploading to Drive: {e}")
            return None
