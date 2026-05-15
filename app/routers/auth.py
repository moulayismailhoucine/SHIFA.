"""Auth router — login, NFC login, logout."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
import bcrypt as _bcrypt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user, bearer
from app.models import User, Patient, AuthToken, Doctor, Pharmacy, Laboratory
from app.schemas import StaffLoginRequest, NfcLoginRequest, TokenResponse

from pydantic import BaseModel

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

router = APIRouter(prefix="/api", tags=["Auth"])
settings = get_settings()
def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _create_jwt(payload: dict) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload.update({"exp": expire, "iat": now})
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _store_token(db: Session, token: str, user_id: int = None, patient_id: int = None):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    record = AuthToken(
        user_id=user_id,
        patient_id=patient_id,
        token=token,
        expires_at=expire,
    )
    db.add(record)
    db.commit()


@router.post("/login", response_model=TokenResponse)
def staff_login(body: StaffLoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            (User.username == body.username) | (User.email == body.username),
            User.is_active == True,
        )
        .first()
    )
    if not user or not _verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _create_jwt({"sub": str(user.id), "role": user.role.value})
    _store_token(db, token, user_id=user.id)

    # Build profile with associated entity
    profile: dict = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "username": user.username,
        "role": user.role.value,
        "avatar": user.avatar,
    }

    if user.role.value == "doctor" and user.doctor:
        d = user.doctor
        profile["doctor"] = {
            "id": d.id,
            "specialty": d.specialty,
            "license_number": d.license_number,
            "working_days": d.working_days,
        }
    elif user.role.value == "pharmacy" and user.pharmacy:
        ph = user.pharmacy
        profile["pharmacy"] = {"id": ph.id, "name": ph.name}
    elif user.role.value == "laboratory" and user.laboratory:
        lab = user.laboratory
        profile["laboratory"] = {"id": lab.id, "name": lab.name}

    return TokenResponse(token=token, user=profile)


@router.post("/nfc-login", response_model=TokenResponse)
def nfc_login(body: NfcLoginRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.nfc_uid == body.nfc_uid,
        Patient.is_active == True,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient with this NFC card not found")

    token = _create_jwt({"patient_id": str(patient.id), "role": "patient"})
    _store_token(db, token, patient_id=patient.id)

    profile = {
        "id": patient.id,
        "name": patient.name,
        "blood_type": patient.blood_type,
        "gender": patient.gender,
        "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
        # Explicitly never expose raw nfc_uid
    }
    return TokenResponse(token=token, patient=profile)


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    new_hash = _bcrypt.hashpw(body.new_password.encode(), _bcrypt.gensalt()).decode()
    current_user.password_hash = new_hash
    db.commit()
    return {"success": True, "message": "Password changed successfully"}

@router.post("/logout")
def logout(
    credentials=Depends(bearer),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    record = db.query(AuthToken).filter(AuthToken.token == token).first()
    if record:
        record.revoked = True
        db.commit()
    return {"success": True, "message": "Logged out successfully"}
