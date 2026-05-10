"""Nursing Orders router — doctor sends care orders to nurses."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import NursingOrder, User, Patient, Doctor

router = APIRouter(prefix="/api/nursing-orders", tags=["Nursing Orders"])


# ── Schemas ─────────────────────────────────────────────────────────

class NursingOrderCreate(BaseModel):
    patient_id: int
    order_type: str = "medication"       # medication | monitoring | care | other
    title: str
    description: Optional[str] = None
    medication_method: Optional[str] = None  # oral | injection | iv | topical | inhalation | subcutaneous | rectal | other
    priority: str = "routine"            # routine | urgent | stat
    nurse_id: Optional[int] = None
    due_at: Optional[datetime] = None


class NursingOrderUpdate(BaseModel):
    status: Optional[str] = None
    completion_note: Optional[str] = None
    nurse_id: Optional[int] = None
    due_at: Optional[datetime] = None


def _serialize(o: NursingOrder) -> dict:
    return {
        "id": o.id,
        "patient_id": o.patient_id,
        "patient_name": o.patient.name if o.patient else None,
        "doctor_id": o.doctor_id,
        "doctor_name": o.doctor.user.name if o.doctor and o.doctor.user else None,
        "nurse_id": o.nurse_id,
        "order_type": o.order_type,
        "title": o.title,
        "description": o.description,
        "medication_method": o.medication_method,
        "priority": o.priority.value if hasattr(o.priority, "value") else o.priority,
        "status": o.status.value if hasattr(o.status, "value") else o.status,
        "due_at": o.due_at.isoformat() if o.due_at else None,
        "completed_at": o.completed_at.isoformat() if o.completed_at else None,
        "completed_by": o.completed_by,
        "completion_note": o.completion_note,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("", status_code=201)
def create_order(
    body: NursingOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor")),
):
    """Doctor creates a nursing order for a patient."""
    try:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor and current_user.role.value == "doctor":
            doctor = Doctor(user_id=current_user.id, specialty="General", department="General")
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
            
        if not doctor and current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Only doctors can create nursing orders")

        # admin fallback: use first doctor
        if not doctor:
            doctor = db.query(Doctor).first()
        if not doctor:
            raise HTTPException(status_code=400, detail="No doctor profile found")

        patient = db.query(Patient).filter(Patient.id == body.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        order = NursingOrder(
            patient_id=body.patient_id,
            doctor_id=doctor.id,
            nurse_id=body.nurse_id,
            order_type=body.order_type,
            title=body.title,
            description=body.description,
            medication_method=body.medication_method if body.order_type == "medication" else None,
            priority=body.priority,
            due_at=body.due_at,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        # reload with relationships
        order = db.query(NursingOrder).options(
            joinedload(NursingOrder.patient), joinedload(NursingOrder.doctor).joinedload(Doctor.user)
        ).filter(NursingOrder.id == order.id).first()
        return {"success": True, "data": _serialize(order)}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("")
def list_orders(
    patient_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List nursing orders. Nurses see pending/in-progress. Doctors see their orders."""
    q = db.query(NursingOrder).options(
        joinedload(NursingOrder.patient), joinedload(NursingOrder.doctor).joinedload(Doctor.user)
    )

    if patient_id:
        q = q.filter(NursingOrder.patient_id == patient_id)

    if status:
        q = q.filter(NursingOrder.status == status)

    # Doctors see only their own orders
    if current_user.role.value == "doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor:
            q = q.filter(NursingOrder.doctor_id == doctor.id)

    orders = q.order_by(NursingOrder.created_at.desc()).limit(limit).all()
    return {"success": True, "data": [_serialize(o) for o in orders]}


@router.patch("/{order_id}")
def update_order(
    order_id: int,
    body: NursingOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Nurse updates status; doctor can reassign nurse or update due date."""
    order = db.query(NursingOrder).filter(NursingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    data = body.model_dump(exclude_unset=True)

    # Auto-set completed_at and completed_by
    if data.get("status") == "completed":
        data["completed_at"] = datetime.now(timezone.utc)
        data["completed_by"] = current_user.id
    elif data.get("status") == "in_progress" and order.nurse_id is None:
        data["nurse_id"] = current_user.id

    for k, v in data.items():
        setattr(order, k, v)

    db.commit()
    db.refresh(order)
    order = db.query(NursingOrder).options(
        joinedload(NursingOrder.patient), joinedload(NursingOrder.doctor).joinedload(Doctor.user)
    ).filter(NursingOrder.id == order_id).first()
    return {"success": True, "data": _serialize(order)}


@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor")),
):
    order = db.query(NursingOrder).filter(NursingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(order)
    db.commit()
