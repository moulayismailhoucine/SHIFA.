"""Doctor-scoped endpoints for managing own nurses and profile."""

from typing import Optional

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import User, Doctor, Nurse, RoleEnum
from app.schemas import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/api/doctor", tags=["Doctor"])


def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


@router.get("/nurses")
def list_my_nurses(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("doctor")),
):
    doctor = current_user.doctor
    if not doctor:
        raise HTTPException(status_code=400, detail="Doctor profile not found")

    nurses = (
        db.query(User)
        .filter(User.role == RoleEnum.nurse)
        .join(Nurse, Nurse.user_id == User.id)
        .filter(Nurse.doctor_id == doctor.id)
        .options(joinedload(User.nurse))
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = (
        db.query(User)
        .filter(User.role == RoleEnum.nurse)
        .join(Nurse, Nurse.user_id == User.id)
        .filter(Nurse.doctor_id == doctor.id)
        .count()
    )
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
                }
                for u in nurses
            ],
        },
    }


@router.post("/nurses", status_code=201)
def create_my_nurse(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("doctor")),
):
    doctor = current_user.doctor
    if not doctor:
        raise HTTPException(status_code=400, detail="Doctor profile not found")

    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=body.name,
        email=body.email,
        username=body.username,
        password_hash=_hash_password(body.password),
        role=RoleEnum.nurse,
        is_active=body.is_active,
    )
    db.add(user)
    db.flush()

    db.add(Nurse(
        user_id=user.id,
        doctor_id=doctor.id,
        department=body.department,
        phone=body.phone,
        license_number=body.license_number,
        shift=body.shift,
    ))

    db.commit()
    db.refresh(user)
    return {"success": True, "data": UserOut.model_validate(user)}


@router.get("/nurses/{nurse_id}")
def get_my_nurse(
    nurse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("doctor")),
):
    doctor = current_user.doctor
    if not doctor:
        raise HTTPException(status_code=400, detail="Doctor profile not found")

    u = (
        db.query(User)
        .filter(User.id == nurse_id, User.role == RoleEnum.nurse)
        .join(Nurse, Nurse.user_id == User.id)
        .filter(Nurse.doctor_id == doctor.id)
        .options(joinedload(User.nurse))
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
        },
    }


@router.patch("/nurses/{nurse_id}")
def update_my_nurse(
    nurse_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("doctor")),
):
    doctor = current_user.doctor
    if not doctor:
        raise HTTPException(status_code=400, detail="Doctor profile not found")

    u = (
        db.query(User)
        .filter(User.id == nurse_id, User.role == RoleEnum.nurse)
        .join(Nurse, Nurse.user_id == User.id)
        .filter(Nurse.doctor_id == doctor.id)
        .first()
    )
    if not u:
        raise HTTPException(status_code=404, detail="Nurse not found")

    data = body.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = _hash_password(data.pop("password"))

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
def delete_my_nurse(
    nurse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("doctor")),
):
    doctor = current_user.doctor
    if not doctor:
        raise HTTPException(status_code=400, detail="Doctor profile not found")

    u = (
        db.query(User)
        .filter(User.id == nurse_id, User.role == RoleEnum.nurse)
        .join(Nurse, Nurse.user_id == User.id)
        .filter(Nurse.doctor_id == doctor.id)
        .first()
    )
    if not u:
        raise HTTPException(status_code=404, detail="Nurse not found")
    db.delete(u)
    db.commit()
