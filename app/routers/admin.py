"""Admin router — user management, doctors, nurses, contact messages, fraud attempts, alerts."""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
import bcrypt as _bcrypt
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_admin
from app.models import User, ContactMessage, FraudAttempt, Alert, Doctor, Pharmacy, Laboratory, Nurse, RoleEnum
from app.schemas import UserCreate, UserUpdate, UserOut
from app.services.storage import save_doctor_photo, file_url, delete_file

router = APIRouter(prefix="/api/admin", tags=["Admin"])
def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


class DoctorProfileUpdate(BaseModel):
    specialty: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    bio: Optional[str] = None
    working_days: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    treatment_time: Optional[int] = None
    clinic_address: Optional[str] = None


# ─────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return {"success": True, "data": {"total": total, "items": [UserOut.model_validate(u) for u in items]}}


@router.post("/users", status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        name=body.name,
        email=body.email,
        username=body.username,
        password_hash=_hash_password(body.password),
        role=body.role,
        is_active=body.is_active,
    )
    db.add(user)
    db.flush()

    # Create linked profile
    if body.role == "doctor":
        db.add(Doctor(user_id=user.id))
    elif body.role == "pharmacy":
        db.add(Pharmacy(user_id=user.id, name=body.name))
    elif body.role == "laboratory":
        db.add(Laboratory(user_id=user.id, name=body.name))
    elif body.role == "nurse":
        db.add(Nurse(
            user_id=user.id,
            doctor_id=body.doctor_id,
            department=body.department,
            phone=body.phone,
            license_number=body.license_number,
            shift=body.shift,
        ))

    db.commit()
    db.refresh(user)
    return {"success": True, "data": UserOut.model_validate(user)}


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data = body.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = _hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return {"success": True, "data": UserOut.model_validate(user)}


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(user)
    db.commit()


# ─────────────────────────────────────────────────────────────────
# Contact messages
# ─────────────────────────────────────────────────────────────────

@router.get("/messages")
def list_messages(
    status: Optional[str] = None,
    email: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(ContactMessage)
    if status:
        q = q.filter(ContactMessage.status == status)
    if email:
        q = q.filter(ContactMessage.email.ilike(f"%{email}%"))
    total = q.count()
    items = q.order_by(ContactMessage.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "success": True,
        "data": {
            "total": total,
            "items": [
                {
                    "id": m.id, "name": m.name, "email": m.email,
                    "subject": m.subject, "message": m.message,
                    "status": m.status.value, "created_at": m.created_at.isoformat(),
                }
                for m in items
            ],
        },
    }


@router.patch("/messages/{msg_id}")
def update_message_status(
    msg_id: int,
    status: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    msg = db.query(ContactMessage).filter(ContactMessage.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Not found")
    msg.status = status
    db.commit()
    return {"success": True, "message": "Status updated"}


@router.delete("/messages/{msg_id}", status_code=204)
def delete_message(
    msg_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    msg = db.query(ContactMessage).filter(ContactMessage.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(msg)
    db.commit()


# ─────────────────────────────────────────────────────────────────
# Fraud attempts
# ─────────────────────────────────────────────────────────────────

@router.get("/fraud-attempts")
def list_fraud_attempts(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    items = (
        db.query(FraudAttempt)
        .order_by(FraudAttempt.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "success": True,
        "data": [
            {
                "id": f.id,
                "appointment_id": f.appointment_id,
                "ip_address": f.ip_address,
                "risk_level": f.risk_level,
                "score": f.score,
                "reason": f.reason,
                "was_blocked": f.was_blocked,
                "created_at": f.created_at.isoformat(),
            }
            for f in items
        ],
    }


# ─────────────────────────────────────────────────────────────────
# Alerts
# ─────────────────────────────────────────────────────────────────

@router.get("/alerts")
def list_alerts(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(Alert)
    if unread_only:
        q = q.filter(Alert.is_read == False)
    alerts = q.order_by(Alert.created_at.desc()).limit(100).all()
    return {
        "success": True,
        "data": [
            {
                "id": a.id, "title": a.title, "message": a.message,
                "level": a.level, "is_read": a.is_read,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
    }


@router.patch("/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Not found")
    alert.is_read = True
    db.commit()
    return {"success": True}


# ─────────────────────────────────────────────────────────────────
# Doctors management
# ─────────────────────────────────────────────────────────────────

@router.get("/doctors")
def list_doctors(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    doctors = (
        db.query(Doctor)
        .options(joinedload(Doctor.user))
        .offset(skip).limit(limit).all()
    )
    total = db.query(Doctor).count()
    return {
        "success": True,
        "data": {
            "total": total,
            "items": [
                {
                    "id": d.id,
                    "user_id": d.user_id,
                    "name": d.user.name,
                    "email": d.user.email,
                    "is_active": d.user.is_active,
                    "specialty": d.specialty,
                    "phone": d.phone,
                    "license_number": d.license_number,
                    "bio": d.bio,
                    "working_days": d.working_days,
                    "working_hours_start": d.working_hours_start,
                    "working_hours_end": d.working_hours_end,
                    "break_start": d.break_start,
                    "break_end": d.break_end,
                    "treatment_time": d.treatment_time,
                    "clinic_address": d.clinic_address,
                    "avatar_url": file_url(d.avatar) if d.avatar else None,
                }
                for d in doctors
            ],
        },
    }


@router.get("/doctors/{doctor_id}")
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    d = db.query(Doctor).options(joinedload(Doctor.user)).filter(Doctor.id == doctor_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {
        "success": True,
        "data": {
            "id": d.id, "user_id": d.user_id,
            "name": d.user.name, "email": d.user.email, "is_active": d.user.is_active,
            "specialty": d.specialty, "phone": d.phone, "license_number": d.license_number,
            "bio": d.bio, "working_days": d.working_days,
            "working_hours_start": d.working_hours_start, "working_hours_end": d.working_hours_end,
            "break_start": d.break_start, "break_end": d.break_end,
            "treatment_time": d.treatment_time, "clinic_address": d.clinic_address,
        },
    }


@router.patch("/doctors/{doctor_id}")
def update_doctor_profile(
    doctor_id: int,
    body: DoctorProfileUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    d = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Doctor not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    db.commit()
    return {"success": True, "message": "Doctor profile updated"}


@router.post("/doctors/{doctor_id}/photo")
async def upload_doctor_photo(
    doctor_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    d = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if d.avatar:
        delete_file(d.avatar)
    relative, _ = await save_doctor_photo(file)
    d.avatar = relative
    db.commit()
    return {"success": True, "avatar_url": file_url(relative)}


@router.patch("/doctors/{doctor_id}/toggle-active")
def toggle_doctor_active(
    doctor_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    d = db.query(Doctor).options(joinedload(Doctor.user)).filter(Doctor.id == doctor_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Doctor not found")
    d.user.is_active = not d.user.is_active
    db.commit()
    return {"success": True, "is_active": d.user.is_active}


@router.delete("/doctors/{doctor_id}", status_code=204)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    d = db.query(Doctor).options(joinedload(Doctor.user)).filter(Doctor.id == doctor_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Doctor not found")
    db.delete(d.user)   # CASCADE removes Doctor row too
    db.commit()


# ─────────────────────────────────────────────────────────────────
# Nurses management
# ─────────────────────────────────────────────────────────────────

@router.get("/nurses")
def list_nurses(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    nurses = (
        db.query(User)
        .filter(User.role == RoleEnum.nurse)
        .options(joinedload(User.nurse).joinedload(Nurse.doctor))
        .offset(skip).limit(limit).all()
    )
    total = db.query(User).filter(User.role == RoleEnum.nurse).count()
    return {
        "success": True,
        "data": {
            "total": total,
            "items": [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "username": u.username,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat(),
                    "department": u.nurse.department if u.nurse else None,
                    "shift": u.nurse.shift if u.nurse else None,
                    "phone": u.nurse.phone if u.nurse else None,
                    "license_number": u.nurse.license_number if u.nurse else None,
                    "doctor_id": u.nurse.doctor_id if u.nurse else None,
                    "doctor_name": u.nurse.doctor.user.name if u.nurse and u.nurse.doctor and u.nurse.doctor.user else None,
                }
                for u in nurses
            ],
        },
    }


@router.get("/nurses/{nurse_id}")
def get_nurse(
    nurse_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    u = (
        db.query(User)
        .filter(User.id == nurse_id, User.role == RoleEnum.nurse)
        .options(joinedload(User.nurse).joinedload(Nurse.doctor))
        .first()
    )
    if not u:
        raise HTTPException(status_code=404, detail="Nurse not found")
    return {
        "success": True,
        "data": {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "username": u.username,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
            "department": u.nurse.department if u.nurse else None,
            "shift": u.nurse.shift if u.nurse else None,
            "phone": u.nurse.phone if u.nurse else None,
            "license_number": u.nurse.license_number if u.nurse else None,
            "doctor_id": u.nurse.doctor_id if u.nurse else None,
            "doctor_name": u.nurse.doctor.user.name if u.nurse and u.nurse.doctor and u.nurse.doctor.user else None,
        },
    }


@router.patch("/nurses/{nurse_id}/toggle-active")
def toggle_nurse_active(
    nurse_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    u = db.query(User).filter(User.id == nurse_id, User.role == RoleEnum.nurse).first()
    if not u:
        raise HTTPException(status_code=404, detail="Nurse not found")
    u.is_active = not u.is_active
    db.commit()
    return {"success": True, "is_active": u.is_active}


@router.patch("/nurses/{nurse_id}")
def update_nurse(
    nurse_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    u = db.query(User).filter(User.id == nurse_id, User.role == RoleEnum.nurse).first()
    if not u:
        raise HTTPException(status_code=404, detail="Nurse not found")
    data = body.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = _hash_password(data.pop("password"))

    # Separate nurse profile fields
    nurse_fields = {"doctor_id", "department", "phone", "license_number", "shift"}
    user_data = {k: v for k, v in data.items() if k not in nurse_fields}
    nurse_data = {k: v for k, v in data.items() if k in nurse_fields}

    for k, v in user_data.items():
        setattr(u, k, v)

    if nurse_data:
        if not u.nurse:
            db.add(Nurse(user_id=u.id, **nurse_data))
        else:
            for k, v in nurse_data.items():
                setattr(u.nurse, k, v)

    db.commit()
    db.refresh(u)
    return {"success": True, "data": UserOut.model_validate(u)}


@router.delete("/nurses/{nurse_id}", status_code=204)
def delete_nurse(
    nurse_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    u = db.query(User).filter(User.id == nurse_id, User.role == RoleEnum.nurse).first()
    if not u:
        raise HTTPException(status_code=404, detail="Nurse not found")
    db.delete(u)
    db.commit()


# ─────────────────────────────────────────────────────────────────
# Laboratories management
# ─────────────────────────────────────────────────────────────────

class LaboratoryProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None


@router.get("/laboratories")
def list_laboratories(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    labs = (
        db.query(Laboratory)
        .options(joinedload(Laboratory.user))
        .offset(skip).limit(limit).all()
    )
    total = db.query(Laboratory).count()
    return {
        "success": True,
        "data": {
            "total": total,
            "items": [
                {
                    "id": lab.id,
                    "user_id": lab.user_id,
                    "name": lab.user.name,
                    "email": lab.user.email,
                    "username": lab.user.username,
                    "is_active": lab.user.is_active,
                    "created_at": lab.user.created_at.isoformat(),
                    "lab_name": lab.name,
                    "address": lab.address,
                    "phone": lab.phone,
                    "license_number": lab.license_number,
                }
                for lab in labs
            ],
        },
    }


@router.get("/laboratories/{lab_id}")
def get_laboratory(
    lab_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    lab = db.query(Laboratory).options(joinedload(Laboratory.user)).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    return {
        "success": True,
        "data": {
            "id": lab.id,
            "user_id": lab.user_id,
            "name": lab.user.name,
            "email": lab.user.email,
            "username": lab.user.username,
            "is_active": lab.user.is_active,
            "created_at": lab.user.created_at.isoformat(),
            "lab_name": lab.name,
            "address": lab.address,
            "phone": lab.phone,
            "license_number": lab.license_number,
        },
    }


@router.patch("/laboratories/{lab_id}")
def update_laboratory(
    lab_id: int,
    body: LaboratoryProfileUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    lab = db.query(Laboratory).options(joinedload(Laboratory.user)).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    data = body.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = _hash_password(data.pop("password"))

    lab_fields = {"address", "phone", "license_number"}
    user_data = {k: v for k, v in data.items() if k not in lab_fields}
    lab_data = {k: v for k, v in data.items() if k in lab_fields}

    for k, v in user_data.items():
        setattr(lab.user, k, v)

    if lab_data:
        for k, v in lab_data.items():
            setattr(lab, k, v)

    db.commit()
    db.refresh(lab)
    return {"success": True, "data": UserOut.model_validate(lab.user)}


@router.patch("/laboratories/{lab_id}/toggle-active")
def toggle_laboratory_active(
    lab_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    lab = db.query(Laboratory).options(joinedload(Laboratory.user)).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    lab.user.is_active = not lab.user.is_active
    db.commit()
    return {"success": True, "is_active": lab.user.is_active}


@router.delete("/laboratories/{lab_id}", status_code=204)
def delete_laboratory(
    lab_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    lab = db.query(Laboratory).options(joinedload(Laboratory.user)).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    db.delete(lab.user)
    db.commit()
