"""Public API router — doctors list, available slots, guest booking, contact, chat."""

import html
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Doctor, Appointment, ContactMessage, Chat
)
from app.schemas import (
    PublicBookingRequest, ContactCreate, ChatRequest, ChatResponse, SuccessResponse, AppointmentOut
)
from app.services.booking import get_available_slots, validate_slot
from app.services.fraud import calculate_fraud_score, log_fraud_attempt
from app.services.ai_chat import get_ai_reply, DISCLAIMER

router = APIRouter(prefix="/api/public", tags=["Public"])
limiter = Limiter(key_func=get_remote_address)


# ─────────────────────────────────────────────────────────────────
# Doctors — public list for booking form
# ─────────────────────────────────────────────────────────────────

@router.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctor).join(Doctor.user).filter(Doctor.user.has(is_active=True)).all()
    return {
        "success": True,
        "data": [
            {
                "id": d.id,
                "name": d.user.name,
                "specialty": d.specialty,
                "avatar": d.avatar or d.user.avatar,
                "working_days": d.working_days,
                "working_hours_start": d.working_hours_start,
                "working_hours_end": d.working_hours_end,
                "treatment_time": d.treatment_time,
                "clinic_address": d.clinic_address,
            }
            for d in doctors
        ],
    }


# ─────────────────────────────────────────────────────────────────
# Available slots
# ─────────────────────────────────────────────────────────────────

@router.get("/available-slots")
def available_slots(
    doctor_id: int,
    date: str,
    db: Session = Depends(get_db),
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD")

    slots = get_available_slots(db, doctor_id, target_date)
    return {"success": True, "data": {"slots": slots}}


# ─────────────────────────────────────────────────────────────────
# Public guest booking
# ─────────────────────────────────────────────────────────────────

@router.post("/book-appointment", status_code=201)
@limiter.limit("5/minute")
def public_book_appointment(
    request: Request,
    body: PublicBookingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Honeypot check
    if body.website or body.confirm_email:
        raise HTTPException(status_code=403, detail="Booking rejected.")

    # Sanitize guest input
    guest_name = html.escape(body.guest_name.strip())
    guest_phone = body.guest_phone.strip()
    guest_email = html.escape(body.guest_email.strip()) if body.guest_email else None
    reason = html.escape(body.reason.strip()) if body.reason else None

    # Validate doctor and slot
    doctor = db.query(Doctor).filter(Doctor.id == body.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    slot_error = validate_slot(db, doctor, body.scheduled_at)
    if slot_error:
        raise HTTPException(status_code=422, detail=slot_error)

    # Fraud detection
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    fraud = calculate_fraud_score(db, ip, guest_phone, guest_email, ua)

    if fraud["is_blocked"]:
        background_tasks.add_task(
            log_fraud_attempt,
            db, None, ip, ua,
            {"guest_phone": guest_phone, "guest_email": guest_email, "doctor_id": body.doctor_id},
            fraud,
        )
        raise HTTPException(
            status_code=429,
            detail="Your booking request has been flagged. Please contact us directly.",
        )

    # Create appointment
    appt = Appointment(
        doctor_id=body.doctor_id,
        scheduled_at=body.scheduled_at,
        reason=reason,
        guest_name=guest_name,
        guest_phone=guest_phone,
        guest_email=guest_email,
        device_id=body.device_id,
        booking_ip=ip,
        booking_ua=ua,
        is_suspicious=fraud["is_suspicious"],
        fraud_score=fraud["score"],
        fraud_risk_level=fraud["risk_level"],
        fraud_reason=fraud["reason_text"],
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # Log fraud attempt if suspicious (but not blocked)
    if fraud["is_suspicious"]:
        background_tasks.add_task(
            log_fraud_attempt,
            db, appt.id, ip, ua,
            {"guest_phone": guest_phone, "guest_email": guest_email},
            fraud,
        )

    return {
        "success": True,
        "message": "Appointment request submitted successfully.",
        "data": {
            "id": appt.id,
            "scheduled_at": appt.scheduled_at.isoformat(),
            "status": appt.status.value,
            "fraud_risk_level": appt.fraud_risk_level,
        },
    }


# ─────────────────────────────────────────────────────────────────
# Public user appointments (no account needed)
# ─────────────────────────────────────────────────────────────────

@router.get("/my-appointments")
def get_public_appointments(
    device_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return appointments for a public user identified by device_id."""
    if not device_id or len(device_id) < 8:
        raise HTTPException(status_code=400, detail="Invalid device_id")

    q = db.query(Appointment).filter(Appointment.device_id == device_id)
    if status:
        q = q.filter(Appointment.status == status)

    items = q.order_by(Appointment.scheduled_at.desc()).limit(50).all()
    return {"success": True, "data": {"total": len(items), "items": [AppointmentOut.model_validate(a) for a in items]}}


# ─────────────────────────────────────────────────────────────────
# Contact form
# ─────────────────────────────────────────────────────────────────

@router.post("/contact", status_code=201)
@limiter.limit("5/minute")
def submit_contact(
    request: Request,
    body: ContactCreate,
    db: Session = Depends(get_db),
):
    # Honeypot
    if body.website:
        raise HTTPException(status_code=403, detail="Rejected.")

    ip = request.client.host if request.client else None
    msg = ContactMessage(
        name=html.escape(body.name),
        email=body.email,
        subject=html.escape(body.subject) if body.subject else None,
        message=html.escape(body.message),
        ip_address=ip,
    )
    db.add(msg)
    db.commit()
    return {"success": True, "message": "Message received. We will get back to you shortly."}


# ─────────────────────────────────────────────────────────────────
# xAI connection test (temporary diagnostic)
# ─────────────────────────────────────────────────────────────────

@router.get("/test-ai")
async def test_ai():
    import httpx
    from app.config import get_settings
    s = get_settings()
    if not s.xai_api_key:
        return {"status": "error", "detail": "XAI_API_KEY not set"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {s.xai_api_key}", "Content-Type": "application/json"},
                json={"model": s.xai_model, "messages": [{"role": "user", "content": "say hi"}], "max_tokens": 10},
            )
            return {"status": resp.status_code, "model": s.xai_model, "body": resp.json()}
    except Exception as exc:
        return {"status": "exception", "detail": str(exc)}


# ─────────────────────────────────────────────────────────────────
# AI medical chat (public — audit logged)
# ─────────────────────────────────────────────────────────────────

@router.post("/medical-chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def medical_chat(
    request: Request,
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    reply, provider = await get_ai_reply(body.message)

    def _log():
        chat = Chat(
            session_id=body.session_id,
            message=body.message,
            response=reply,
            provider_used=provider,
        )
        db.add(chat)
        db.commit()

    background_tasks.add_task(_log)

    return ChatResponse(reply=reply, provider=provider, disclaimer=DISCLAIMER)
