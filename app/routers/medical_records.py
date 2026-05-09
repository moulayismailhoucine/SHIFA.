"""Medical records, vitals, nurse notes routers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import MedicalRecord, VitalSign, NurseNote, User
from app.schemas import (
    MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordOut,
    VitalSignCreate, VitalSignOut, NurseNoteCreate, NurseNoteOut,
)

router = APIRouter(prefix="/api", tags=["Clinical Records"])


# ─────────────────────────────────────────────────────────────────
# Medical Records
# ─────────────────────────────────────────────────────────────────

@router.get("/medical-records")
def list_medical_records(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.visit_date.desc())
        .all()
    )
    return {"success": True, "data": [MedicalRecordOut.model_validate(r) for r in records]}


@router.get("/medical-records/{record_id}")
def get_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return {"success": True, "data": MedicalRecordOut.model_validate(record)}


@router.post("/medical-records", status_code=201)
def create_medical_record(
    body: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor")),
):
    record = MedicalRecord(**body.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"success": True, "data": MedicalRecordOut.model_validate(record)}


@router.patch("/medical-records/{record_id}")
def update_medical_record(
    record_id: int,
    body: MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor")),
):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(record, k, v)
    db.commit()
    db.refresh(record)
    return {"success": True, "data": MedicalRecordOut.model_validate(record)}


@router.delete("/medical-records/{record_id}", status_code=204)
def delete_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(record)
    db.commit()


# ─────────────────────────────────────────────────────────────────
# Vital Signs
# ─────────────────────────────────────────────────────────────────

@router.post("/vitals", status_code=201)
def record_vital_signs(
    body: VitalSignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "nurse")),
):
    vital = VitalSign(**body.model_dump(), recorded_by=current_user.id)
    db.add(vital)
    db.commit()
    db.refresh(vital)
    return {"success": True, "data": VitalSignOut.model_validate(vital)}


@router.get("/vitals/{patient_id}")
def get_patient_vitals(
    patient_id: int,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vitals = (
        db.query(VitalSign)
        .filter(VitalSign.patient_id == patient_id)
        .order_by(VitalSign.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return {"success": True, "data": [VitalSignOut.model_validate(v) for v in vitals]}


# ─────────────────────────────────────────────────────────────────
# Nurse Notes
# ─────────────────────────────────────────────────────────────────

@router.post("/nurse-notes", status_code=201)
def create_nurse_note(
    body: NurseNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "nurse")),
):
    note = NurseNote(patient_id=body.patient_id, nurse_id=current_user.id, note=body.note)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"success": True, "data": NurseNoteOut.model_validate(note)}


@router.get("/nurse-notes/{patient_id}")
def get_nurse_notes(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notes = (
        db.query(NurseNote)
        .filter(NurseNote.patient_id == patient_id)
        .order_by(NurseNote.created_at.desc())
        .all()
    )
    return {"success": True, "data": [NurseNoteOut.model_validate(n) for n in notes]}
