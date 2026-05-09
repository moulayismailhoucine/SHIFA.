"""AI router — X-ray analysis endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import LabResult, User
from app.services.storage import file_url

router = APIRouter(prefix="/api/ai", tags=["AI Analysis"])

# Lazy import to avoid TF startup cost
_ai_module = None


def _get_ai():
    global _ai_module
    if _ai_module is None:
        try:
            from app.ai import analyze_xray
            _ai_module = analyze_xray
        except Exception:
            _ai_module = False
    return _ai_module


@router.post("/analyze-xray/{result_id}")
def analyze_xray_endpoint(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "laboratory")),
):
    """Trigger AI analysis on an existing lab result X-ray."""
    result = db.query(LabResult).filter(LabResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Lab result not found")

    if result.category not in ("xray", "ct_scan"):
        raise HTTPException(status_code=400, detail="AI analysis only available for X-ray/CT images")

    analyze = _get_ai()
    if analyze is False:
        raise HTTPException(status_code=503, detail="AI model not available. Train the model first.")

    # Resolve full file path
    from app.config import get_settings
    settings = get_settings()
    uploads_dir = Path(settings.upload_dir) if hasattr(settings, "upload_dir") else Path("uploads")
    image_path = uploads_dir / result.file_path

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    # Run inference
    ai_result = analyze(str(image_path))
    if ai_result is None:
        raise HTTPException(status_code=500, detail="AI analysis failed")

    # Save results to DB
    result.ai_diagnosis = ai_result["diagnosis"]
    result.ai_probability = ai_result["probability"]
    result.ai_note = ai_result["note"]
    result.ai_model_version = "mura_mobilenetv2_v1"
    from datetime import datetime, timezone
    result.ai_analyzed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "success": True,
        "data": {
            "diagnosis": ai_result["diagnosis"],
            "probability": ai_result["probability"],
            "body_part": ai_result["body_part"],
            "note": ai_result["note"],
            "class_probabilities": ai_result["class_probabilities"],
        },
    }


@router.get("/status")
def ai_status(current_user: User = Depends(get_current_user)):
    """Check if AI model is loaded and ready."""
    analyze = _get_ai()
    ready = analyze is not False
    return {"success": True, "data": {"ready": ready}}
