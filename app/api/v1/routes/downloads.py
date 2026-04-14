import os
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from app.api import deps
from app.core.config import settings

router = APIRouter()

@router.get("/list", response_model=List[str])
def list_files(
    api_key: str = Depends(deps.verify_api_secret),
) -> Any:
    """List all downloaded files recursively."""
    if not os.path.exists(settings.DOWNLOAD_DIR):
        return []
    
    file_list = []
    for root, dirs, files in os.walk(settings.DOWNLOAD_DIR):
        for file in files:
            # Get the path relative to the download directory
            rel_path = os.path.relpath(os.path.join(root, file), settings.DOWNLOAD_DIR)
            file_list.append(rel_path)
    
    return sorted(file_list)

@router.get("/file/{file_path:path}")
def get_file(
    file_path: str,
    api_key: str = Depends(deps.verify_api_secret),
) -> Any:
    """Download a specific file using its relative path."""
    full_path = os.path.join(settings.DOWNLOAD_DIR, file_path)
    
    # Security check to prevent directory traversal
    abs_file_path = os.path.abspath(full_path)
    abs_download_dir = os.path.abspath(settings.DOWNLOAD_DIR)
    
    if not abs_file_path.startswith(abs_download_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forbidden file path"
        )

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    filename = os.path.basename(full_path)
    return FileResponse(full_path, filename=filename)
