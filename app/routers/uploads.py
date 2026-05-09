"""Uploads router — general file upload utilities."""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import get_settings
from app.dependencies import require_roles
from app.models import User
from app.services.storage import file_url

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])
settings = get_settings()


@router.get("/file")
def serve_upload(
    path: str,
    current_user: User = Depends(require_roles("admin", "doctor", "nurse", "pharmacy", "laboratory")),
):
    """Serve an uploaded file by relative path (authenticated access only)."""
    full_path = Path(settings.upload_dir) / path.lstrip("/")
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    # Basic path traversal guard
    try:
        full_path.resolve().relative_to(Path(settings.upload_dir).resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    return FileResponse(str(full_path))
