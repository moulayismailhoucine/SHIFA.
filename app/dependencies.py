"""Auth dependencies — JWT decode, NFC lookup, role enforcement."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User, Patient, AuthToken

settings = get_settings()
logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except Exception as e:
        logger.warning(f"JWT decode failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def _check_revoked(db: Session, token: str) -> AuthToken:
    record = db.query(AuthToken).filter(
        AuthToken.token == token,
        AuthToken.revoked == False,
    ).first()
    if not record:
        logger.warning(f"Token not found in DB (len={len(token)})")
        raise HTTPException(status_code=401, detail="Token revoked or not found")
    now = datetime.now(timezone.utc)
    if record.expires_at.tzinfo is None:
        now = now.replace(tzinfo=None)
    if record.expires_at < now:
        logger.warning(f"Token expired at {record.expires_at}, now is {now}")
        raise HTTPException(status_code=401, detail="Token expired")
    return record


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        logger.warning("No credentials provided")
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    logger.info(f"Auth token received (len={len(token)})")
    payload = _decode_token(token)
    record = _check_revoked(db, token)
    user_id: int = payload.get("sub", 0)
    if not user_id:
        logger.warning("No user_id in token payload")
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found for id={user_id}")
        raise HTTPException(status_code=401, detail="User not found")
    logger.info(f"Authenticated user={user.email} role={user.role}")
    return user


def get_current_patient(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> Patient:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    payload = _decode_token(token)
    _check_revoked(db, token)
    patient_id = payload.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=401, detail="Not a patient token")
    patient = db.query(Patient).filter(Patient.id == int(patient_id), Patient.is_active == True).first()
    if not patient:
        raise HTTPException(status_code=401, detail="Patient not found")
    return patient


def require_roles(*roles: str):
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(roles)}"
            )
        return current_user
    return _dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
