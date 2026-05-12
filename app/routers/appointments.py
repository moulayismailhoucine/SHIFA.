"""Appointments CRUD router."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import Appointment, Doctor, User
from app.schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from app.services.booking import validate_slot

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.get("/my")
def my_appointments(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return appointments for the currently logged-in user."""
    q = db.query(Appointment)

    # Filter by patient_id if user has a patient profile
    if current_user.patient_id:
        q = q.filter(Appointment.patient_id == current_user.patient_id)
    # Otherwise try matching guest info by name + phone
    elif current_user.phone:
        q = q.filter(
            (Appointment.guest_phone == current_user.phone) |
            (Appointment.guest_name.ilike(f"%{current_user.name}%"))
        )
    else:
        q = q.filter(Appointment.guest_name.ilike(f"%{current_user.name}%"))

    if status:
        q = q.filter(Appointment.status == status)

    items = q.order_by(Appointment.scheduled_at.desc()).limit(50).all()
    return {"success": True, "data": {"total": len(items), "items": [AppointmentOut.model_validate(a) for a in items]}}


@router.get("/")
def list_appointments(
    status: Optional[str] = None,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Appointment)
    if status:
        q = q.filter(Appointment.status == status)
    if doctor_id:
        q = q.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        q = q.filter(Appointment.patient_id == patient_id)
    # Doctors can only see their own
    if current_user.role.value == "doctor" and current_user.doctor:
        q = q.filter(Appointment.doctor_id == current_user.doctor.id)

    total = q.count()
    items = q.order_by(Appointment.scheduled_at.desc()).offset(skip).limit(limit).all()
    return {"success": True, "data": {"total": total, "items": [AppointmentOut.model_validate(a) for a in items]}}


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


@router.post("/", status_code=201)
def create_appointment(
    body: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "nurse")),
):
    # Honeypot
    if body.website or body.confirm_email:
        raise HTTPException(status_code=403, detail="Rejected")

    doctor = db.query(Doctor).filter(Doctor.id == body.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    err = validate_slot(db, doctor, body.scheduled_at)
    if err:
        raise HTTPException(status_code=422, detail=err)

    appt = Appointment(
        patient_id=body.patient_id,
        doctor_id=body.doctor_id,
        scheduled_at=body.scheduled_at,
        reason=body.reason,
        notes=body.notes,
        guest_name=body.guest_name,
        guest_phone=body.guest_phone,
        guest_email=body.guest_email,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return {"success": True, "data": AppointmentOut.model_validate(appt)}


@router.patch("/{appointment_id}")
def update_appointment(
    appointment_id: int,
    body: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "nurse")),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if body.scheduled_at and body.scheduled_at != appt.scheduled_at:
        doctor = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        err = validate_slot(db, doctor, body.scheduled_at)
        if err:
            raise HTTPException(status_code=422, detail=err)
        appt.scheduled_at = body.scheduled_at

    if body.status is not None:
        appt.status = body.status
    if body.reason is not None:
        appt.reason = body.reason
    if body.notes is not None:
        appt.notes = body.notes

    db.commit()
    db.refresh(appt)
    return {"success": True, "data": AppointmentOut.model_validate(appt)}


@router.delete("/{appointment_id}", status_code=204)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appt)
    db.commit()
