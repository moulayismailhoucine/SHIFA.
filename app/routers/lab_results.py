"""Lab results router — upload and list."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db

logger = logging.getLogger(__name__)
from app.dependencies import get_current_user, require_roles
from app.models import LabResult, User
from app.schemas import LabResultOut
from app.services.storage import save_lab_result_file, file_url, delete_file
from app.config import get_settings

router = APIRouter(prefix="/api/lab-results", tags=["Lab Results"])


@router.get("/")
def list_lab_results(
    patient_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(LabResult)
    if patient_id:
        q = q.filter(LabResult.patient_id == patient_id)
    if current_user.role.value == "laboratory" and current_user.laboratory:
        q = q.filter(LabResult.laboratory_id == current_user.laboratory.id)
    items = q.order_by(LabResult.created_at.desc()).all()
    return {
        "success": True,
        "data": [
            {**LabResultOut.model_validate(r).model_dump(), "url": file_url(r.file_path)}
            for r in items
        ],
    }


@router.get("/{result_id}")
def get_lab_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(LabResult).filter(LabResult.id == result_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "success": True,
        "data": {**LabResultOut.model_validate(r).model_dump(), "url": file_url(r.file_path)},
    }


def _run_ai_analysis(result_id: int):
    """Background task: run AI analysis on uploaded X-ray."""
    try:
        from app.ai import analyze_xray
        from app.database import SessionLocal
        from datetime import datetime, timezone

        db = SessionLocal()
        try:
            result = db.query(LabResult).filter(LabResult.id == result_id).first()
            if not result or not result.file_path:
                return

            settings = get_settings()
            image_path = Path(settings.upload_dir) / result.file_path
            if not image_path.exists():
                return

            ai_result = analyze_xray(str(image_path))
            if ai_result:
                result.ai_diagnosis = ai_result["diagnosis"]
                result.ai_probability = ai_result["probability"]
                result.ai_note = ai_result["note"]
                result.ai_model_version = "mura_mobilenetv2_v1"
                result.ai_analyzed_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"AI analysis failed for result {result_id}: {e}")


@router.post("/upload", status_code=201)
async def upload_lab_result(
    patient_id: int = Form(...),
    title: str = Form(...),
    category: str = Form(None),
    note: str = Form(None),
    laboratory_id: int = Form(None),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "laboratory")),
):
    relative, mime = await save_lab_result_file(file)

    # Auto-assign laboratory_id from user profile
    if laboratory_id is None and current_user.role.value == "laboratory" and current_user.laboratory:
        laboratory_id = current_user.laboratory.id

    result = LabResult(
        patient_id=patient_id,
        laboratory_id=laboratory_id,
        title=title,
        category=category,
        note=note,
        file_path=relative,
        file_type=mime,
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    # Trigger AI analysis for X-ray / CT scan images
    if category in ("xray", "ct_scan") and background_tasks:
        background_tasks.add_task(_run_ai_analysis, result.id)

    return {
        "success": True,
        "data": {
            **LabResultOut.model_validate(result).model_dump(),
            "url": file_url(relative),
        },
    }


@router.delete("/{result_id}")
def delete_lab_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "laboratory")),
):
    r = db.query(LabResult).filter(LabResult.id == result_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")

    if current_user.role.value == "laboratory":
        if not current_user.laboratory or r.laboratory_id != current_user.laboratory.id:
            raise HTTPException(status_code=403, detail="You can only delete your own results")

    delete_file(r.file_path)
    db.delete(r)
    db.commit()
    return {"success": True}
