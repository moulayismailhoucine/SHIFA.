"""File storage service — validation, save, delete."""

import hashlib
import mimetypes
import os
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile

from app.config import get_settings

settings = get_settings()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_LAB_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/tiff"}
MAX_SIZE_BYTES = settings.max_upload_size_mb * 1024 * 1024


def _sanitize_filename(name: str) -> str:
    name = os.path.basename(name)
    name = re.sub(r"[^\w.\-]", "_", name)
    return name[:100]


def _ensure_dir(subdir: str) -> Path:
    path = Path(settings.upload_dir) / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


async def save_file(
    file: UploadFile,
    subdir: str,
    allowed_types: set,
    max_bytes: int = MAX_SIZE_BYTES,
) -> Tuple[str, str]:
    """
    Validate, save file, return (relative_path, mime_type).
    Raises HTTPException on failure.
    """
    # Read content
    content = await file.read()

    # Size check
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.max_upload_size_mb}MB",
        )

    # Mime check
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"File type not allowed. Allowed: {', '.join(allowed_types)}",
        )

    ext = Path(file.filename or "file").suffix or mimetypes.guess_extension(mime) or ".bin"
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = _ensure_dir(subdir)
    dest_path = dest_dir / safe_name
    dest_path.write_bytes(content)

    relative = f"{subdir}/{safe_name}"
    return relative, mime


def delete_file(relative_path: Optional[str]) -> None:
    if not relative_path:
        return
    full = Path(settings.upload_dir) / relative_path
    if full.exists():
        full.unlink(missing_ok=True)


def file_url(relative_path: Optional[str]) -> Optional[str]:
    if not relative_path:
        return None
    return f"{settings.app_url}/uploads/{relative_path}"


async def save_patient_photo(file: UploadFile) -> Tuple[str, str]:
    return await save_file(file, "patients", ALLOWED_IMAGE_TYPES)


async def save_lab_result_file(file: UploadFile) -> Tuple[str, str]:
    return await save_file(file, "lab_results", ALLOWED_LAB_TYPES)
