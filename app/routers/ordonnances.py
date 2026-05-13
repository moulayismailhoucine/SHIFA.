"""Ordonnances (prescriptions) router — CRUD, PDF, dispense, toggle."""

from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import Ordonnance, User
from app.schemas import OrdonnanceCreate, OrdonnanceUpdate, OrdonnanceOut
from app.services.pdf import generate_ordonnance_pdf
from app.services.storage import file_url

router = APIRouter(prefix="/api/ordonnances", tags=["Ordonnances"])
settings = get_settings()
templates = Jinja2Templates(directory="app/templates")


@router.get("/search")
def search_by_reference(
    ref: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "pharmacy")),
):
    if not ref:
        raise HTTPException(status_code=400, detail="Reference number required")
    o = db.query(Ordonnance).filter(Ordonnance.reference_number == ref.strip().upper()).first()
    if not o:
        raise HTTPException(status_code=404, detail="Ordonnance not found")
    return {"success": True, "data": OrdonnanceOut.model_validate(o)}


@router.get("/{ordonnance_id}/print", response_class=HTMLResponse)
def print_ordonnance(
    ordonnance_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "pharmacy", "nurse")),
):
    o = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    doctor = o.doctor
    patient = o.patient
    logo = doctor.logo_url if doctor and doctor.logo_url else "/static/img/default-logo.svg"
    return templates.TemplateResponse("ordonnances/print.html", {
        "request": request,
        "ordonnance": o,
        "doctor": doctor,
        "patient": patient,
        "logo_url": logo,
        "medications": o.medications or [],
        "now": datetime.utcnow(),
    })


@router.get("/")
def list_ordonnances(
    patient_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Ordonnance)
    if patient_id:
        q = q.filter(Ordonnance.patient_id == patient_id)
    if current_user.role.value == "doctor" and current_user.doctor:
        q = q.filter(Ordonnance.doctor_id == current_user.doctor.id)
    items = q.order_by(Ordonnance.issued_date.desc()).all()
    return {"success": True, "data": [OrdonnanceOut.model_validate(o) for o in items]}


@router.get("/{ordonnance_id}")
def get_ordonnance(
    ordonnance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    o = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Ordonnance not found")
    return {"success": True, "data": OrdonnanceOut.model_validate(o)}


@router.post("/", status_code=201)
def create_ordonnance(
    body: OrdonnanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor")),
):
    from app.models import Doctor
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor and current_user.role.value == "doctor":
        doctor = Doctor(user_id=current_user.id, specialty="General", department="General")
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        
    doctor_id = body.doctor_id
    if current_user.role.value == "doctor":
        if not doctor:
            raise HTTPException(status_code=400, detail="No doctor profile found")
        doctor_id = doctor.id
    elif not doctor_id:
        doc = db.query(Doctor).first()
        if doc: doctor_id = doc.id

    if not doctor_id:
        raise HTTPException(status_code=400, detail="A valid doctor_id is required")

    meds = [m.model_dump() for m in body.medications]
    ref = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
    o = Ordonnance(
        reference_number=ref,
        medical_record_id=body.medical_record_id,
        patient_id=body.patient_id,
        doctor_id=doctor_id,
        medications=meds,
        instructions=body.instructions,
        issued_date=body.issued_date,
        valid_until=body.valid_until,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return {"success": True, "data": OrdonnanceOut.model_validate(o)}


@router.patch("/{ordonnance_id}")
def update_ordonnance(
    ordonnance_id: int,
    body: OrdonnanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor")),
):
    o = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    update_data = body.model_dump(exclude_unset=True)
    if "medications" in update_data and update_data["medications"]:
        update_data["medications"] = [m.model_dump() if hasattr(m, "model_dump") else m for m in update_data["medications"]]
    for k, v in update_data.items():
        setattr(o, k, v)
    db.commit()
    db.refresh(o)
    return {"success": True, "data": OrdonnanceOut.model_validate(o)}


@router.delete("/{ordonnance_id}", status_code=204)
def delete_ordonnance(
    ordonnance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    o = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(o)
    db.commit()


@router.post("/{ordonnance_id}/pdf")
def generate_pdf(
    ordonnance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "pharmacy")),
):
    o = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")

    doctor_name = o.doctor.user.name if o.doctor and o.doctor.user else "Unknown Doctor"
    doctor_specialty = o.doctor.specialty if o.doctor else None
    patient_name = o.patient.name if o.patient else "Unknown Patient"

    relative = generate_ordonnance_pdf(
        ordonnance_id=o.id,
        patient_name=patient_name,
        doctor_name=doctor_name,
        doctor_specialty=doctor_specialty,
        medications=o.medications or [],
        instructions=o.instructions,
        issued_date=o.issued_date,
        valid_until=o.valid_until,
    )

    o.pdf_path = relative
    db.commit()

    return {
        "success": True,
        "data": {
            "path": relative,
            "url": file_url(relative),
        },
    }


@router.get("/{ordonnance_id}/download-pdf")
def download_pdf(
    ordonnance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    o = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not o or not o.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not generated yet")
    full_path = Path(settings.upload_dir) / o.pdf_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(str(full_path), media_type="application/pdf", filename=full_path.name)


@router.post("/{ordonnance_id}/dispense")
def dispense_ordonnance(
    ordonnance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "pharmacy")),
):
    o = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    if o.status.value == "dispensed":
        raise HTTPException(status_code=409, detail="Already dispensed")
    o.status = "dispensed"
    o.dispensed_by = current_user.id
    o.dispensed_at = datetime.utcnow()
    o.is_taken = True
    db.commit()
    return {"success": True, "message": "Ordonnance marked as dispensed"}


@router.patch("/{ordonnance_id}/toggle-taken")
def toggle_taken(
    ordonnance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "pharmacy", "doctor")),
):
    o = db.query(Ordonnance).filter(Ordonnance.id == ordonnance_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    o.is_taken = not o.is_taken
    db.commit()
    return {"success": True, "data": {"is_taken": o.is_taken}}
