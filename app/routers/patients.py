"""Patients CRUD + history + recommendations."""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import Patient, MedicalRecord, Ordonnance, LabResult, VitalSign, User
from app.schemas import PatientCreate, PatientUpdate, PatientOut
from app.services.storage import save_patient_photo, delete_file, file_url

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("/")
def list_patients(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Patient).filter(Patient.is_active == True)
    if search:
        q = q.filter(
            Patient.name.ilike(f"%{search}%")
            | Patient.phone.ilike(f"%{search}%")
            | Patient.email.ilike(f"%{search}%")
            | Patient.nfc_uid.ilike(f"%{search}%")
        )
    total = q.count()
    items = q.order_by(Patient.name).offset(skip).limit(limit).all()
    return {
        "success": True,
        "data": {
            "total": total,
            "items": [PatientOut.model_validate(p) for p in items],
        },
    }


@router.get("/{patient_id}")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"success": True, "data": PatientOut.model_validate(patient)}


@router.post("/", status_code=201)
def create_patient(
    body: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "nurse")),
):
    patient = Patient(**body.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return {"success": True, "data": PatientOut.model_validate(patient)}


@router.patch("/{patient_id}")
def update_patient(
    patient_id: int,
    body: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "nurse")),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(patient, k, v)
    db.commit()
    db.refresh(patient)
    return {"success": True, "data": PatientOut.model_validate(patient)}


@router.delete("/{patient_id}", status_code=204)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.is_active = False
    db.commit()


@router.post("/{patient_id}/photo")
async def upload_patient_photo(
    patient_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "nurse")),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Delete old photo
    delete_file(patient.photo)

    relative, _ = await save_patient_photo(file)
    patient.photo = relative
    db.commit()
    return {
        "success": True,
        "data": {
            "path": relative,
            "url": file_url(relative),
        },
    }


@router.get("/{patient_id}/history")
def patient_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    records = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.visit_date.desc())
        .all()
    )
    ordonnances = (
        db.query(Ordonnance)
        .filter(Ordonnance.patient_id == patient_id)
        .order_by(Ordonnance.issued_date.desc())
        .all()
    )
    lab_results = (
        db.query(LabResult)
        .filter(LabResult.patient_id == patient_id)
        .order_by(LabResult.created_at.desc())
        .all()
    )
    vitals = (
        db.query(VitalSign)
        .filter(VitalSign.patient_id == patient_id)
        .order_by(VitalSign.recorded_at.desc())
        .limit(20)
        .all()
    )

    return {
        "success": True,
        "data": {
            "patient": PatientOut.model_validate(patient),
            "medical_records": [
                {
                    "id": r.id,
                    "visit_date": str(r.visit_date),
                    "visit_type": r.visit_type,
                    "diagnosis": r.diagnosis,
                    "notes": r.notes,
                    "temperature": r.temperature,
                    "blood_pressure": r.blood_pressure,
                    "heart_rate": r.heart_rate,
                }
                for r in records
            ],
            "ordonnances": [
                {
                    "id": o.id,
                    "issued_date": str(o.issued_date),
                    "medications": o.medications,
                    "status": o.status.value,
                    "is_taken": o.is_taken,
                }
                for o in ordonnances
            ],
            "lab_results": [
                {
                    "id": lr.id,
                    "title": lr.title,
                    "file_type": lr.file_type,
                    "category": lr.category,
                    "created_at": lr.created_at.isoformat(),
                    "url": file_url(lr.file_path),
                    "ai_diagnosis": lr.ai_diagnosis,
                    "ai_probability": lr.ai_probability,
                    "ai_note": lr.ai_note,
                    "ai_analyzed_at": lr.ai_analyzed_at.isoformat() if lr.ai_analyzed_at else None,
                    "ai_model_version": lr.ai_model_version,
                }
                for lr in lab_results
            ],
            "vitals_trend": [
                {
                    "recorded_at": v.recorded_at.isoformat(),
                    "temperature": v.temperature,
                    "blood_pressure": v.blood_pressure,
                    "heart_rate": v.heart_rate,
                    "oxygen_saturation": v.oxygen_saturation,
                    "glucose": v.glucose,
                }
                for v in vitals
            ],
        },
    }


@router.get("/{patient_id}/recommendations")
def patient_recommendations(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "laboratory")),
):
    """Generate basic AI-free recommendations from patient data."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    latest_vitals = (
        db.query(VitalSign)
        .filter(VitalSign.patient_id == patient_id)
        .order_by(VitalSign.recorded_at.desc())
        .first()
    )

    recommendations = []

    if latest_vitals:
        if latest_vitals.temperature and latest_vitals.temperature > 38.0:
            recommendations.append({
                "type": "alert",
                "category": "Temperature",
                "message": f"Elevated temperature ({latest_vitals.temperature}°C). Monitor for fever.",
            })
        if latest_vitals.heart_rate:
            if latest_vitals.heart_rate > 100:
                recommendations.append({"type": "alert", "category": "Heart Rate", "message": "Tachycardia detected. Consider cardiology review."})
            elif latest_vitals.heart_rate < 60:
                recommendations.append({"type": "alert", "category": "Heart Rate", "message": "Bradycardia detected. Consider cardiology review."})
        if latest_vitals.oxygen_saturation and latest_vitals.oxygen_saturation < 95:
            recommendations.append({"type": "critical", "category": "O2 Saturation", "message": "Low oxygen saturation. Immediate assessment required."})

    if not recommendations:
        recommendations.append({"type": "info", "category": "General", "message": "Patient vitals appear within normal ranges. Continue routine monitoring."})

    return {"success": True, "data": recommendations}
