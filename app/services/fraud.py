"""Fraud detection service — scoring + risk classification."""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import threading

from sqlalchemy.orm import Session
from app.models import Appointment, FraudAttempt


# ─── In-memory IP rate counter (per-process; swap for Redis in prod) ──────────
_ip_counters: Dict[str, List[datetime]] = defaultdict(list)
_lock = threading.Lock()

WINDOW_MINUTES = 60
MAX_BOOKINGS_PER_IP = 5

TEMP_EMAIL_DOMAINS = {
    "mailinator.com", "10minutemail.com", "guerrillamail.com",
    "trashmail.com", "yopmail.com", "fakeinbox.com", "throwam.com",
}


def _track_ip(ip: str) -> int:
    """Return count of bookings from this IP in the last WINDOW_MINUTES."""
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=WINDOW_MINUTES)
    with _lock:
        _ip_counters[ip] = [t for t in _ip_counters[ip] if t > cutoff]
        _ip_counters[ip].append(now)
        return len(_ip_counters[ip])


def _is_temp_email(email: Optional[str]) -> bool:
    if not email:
        return False
    domain = email.split("@")[-1].lower()
    return domain in TEMP_EMAIL_DOMAINS


def _has_suspicious_phone(phone: Optional[str]) -> bool:
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    # All same digit: 0000000, 1111111...
    if len(set(digits)) <= 2 and len(digits) >= 7:
        return True
    # Sequential ascending/descending
    try:
        diffs = [int(digits[i + 1]) - int(digits[i]) for i in range(len(digits) - 1)]
        if all(d == 1 for d in diffs) or all(d == -1 for d in diffs):
            return True
    except Exception:
        pass
    return False


def _has_duplicate_recent_booking(db: Session, phone: Optional[str], email: Optional[str]) -> bool:
    if not phone and not email:
        return False
    cutoff = datetime.utcnow() - timedelta(hours=2)
    q = db.query(Appointment).filter(Appointment.created_at >= cutoff)
    if phone:
        if q.filter(Appointment.guest_phone == phone).count() > 0:
            return True
    if email:
        if q.filter(Appointment.guest_email == email).count() > 0:
            return True
    return False


def calculate_fraud_score(
    db: Session,
    ip: str,
    guest_phone: Optional[str],
    guest_email: Optional[str],
    ua: str = "",
) -> Dict:
    score = 0
    reasons: List[str] = []

    # 1 — High frequency from same IP
    ip_count = _track_ip(ip)
    if ip_count > MAX_BOOKINGS_PER_IP:
        score += 40
        reasons.append(f"High booking frequency from IP ({ip_count} in {WINDOW_MINUTES}min)")

    # 2 — Duplicate phone/email booking
    if _has_duplicate_recent_booking(db, guest_phone, guest_email):
        score += 35
        reasons.append("Duplicate booking: same phone/email within 2h")

    # 3 — Temp email domain
    if _is_temp_email(guest_email):
        score += 25
        reasons.append("Temporary/disposable email domain")

    # 4 — Suspicious phone
    if _has_suspicious_phone(guest_phone):
        score += 25
        reasons.append("Suspicious phone pattern (repeated/sequential digits)")

    # Classify
    if score >= 50:
        risk = "critical"
    elif score >= 30:
        risk = "high"
    elif score >= 20:
        risk = "medium"
    elif score >= 10:
        risk = "low"
    else:
        risk = "minimal"

    is_blocked = risk in ("critical", "high")

    return {
        "score": score,
        "risk_level": risk,
        "is_suspicious": score >= 10,
        "is_blocked": is_blocked,
        "reasons": reasons,
        "reason_text": "; ".join(reasons) if reasons else None,
    }


def log_fraud_attempt(
    db: Session,
    appointment_id: Optional[int],
    ip: str,
    ua: str,
    payload: dict,
    result: dict,
) -> None:
    attempt = FraudAttempt(
        appointment_id=appointment_id,
        ip_address=ip,
        user_agent=ua,
        payload=payload,
        reason=result.get("reason_text"),
        risk_level=result.get("risk_level"),
        score=result.get("score", 0),
        was_blocked=result.get("is_blocked", False),
    )
    db.add(attempt)
    db.commit()
