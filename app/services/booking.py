"""Booking slot logic — available slot computation."""

from datetime import datetime, date, timedelta, time
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Doctor, Appointment, DoctorUnavailability, AppointmentStatus

DAY_ABBREVS = {
    "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3,
    "Fri": 4, "Sat": 5, "Sun": 6,
}


def _parse_time(t_str: Optional[str]) -> Optional[time]:
    if not t_str:
        return None
    try:
        h, m = t_str.split(":")
        return time(int(h), int(m))
    except Exception:
        return None


def _is_doctor_available_on_date(doctor: Doctor, target_date: date) -> bool:
    """Check working days and unavailability ranges."""
    if doctor.working_days:
        working = [d.strip() for d in doctor.working_days.split(",")]
        weekday = target_date.weekday()  # 0=Mon
        allowed = {DAY_ABBREVS[d] for d in working if d in DAY_ABBREVS}
        if weekday not in allowed:
            return False
    # Check unavailability
    for u in doctor.unavailabilities:
        if u.start_date <= target_date <= u.end_date:
            return False
    return True


def get_available_slots(
    db: Session,
    doctor_id: int,
    target_date: date,
    try_next_day: bool = True,
) -> List[str]:
    """
    Returns list of ISO-format datetime strings for available slots.
    Falls back to next working day if none found.
    """
    doctor: Optional[Doctor] = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return []

    slots = _compute_slots(db, doctor, target_date)
    if not slots and try_next_day:
        # Try up to 14 days ahead
        for delta in range(1, 15):
            next_date = target_date + timedelta(days=delta)
            slots = _compute_slots(db, doctor, next_date)
            if slots:
                break

    return [s.isoformat() for s in slots]


def _compute_slots(db: Session, doctor: Doctor, target_date: date) -> List[datetime]:
    if not _is_doctor_available_on_date(doctor, target_date):
        return []

    start_t = _parse_time(doctor.working_hours_start) or time(8, 0)
    end_t = _parse_time(doctor.working_hours_end) or time(17, 0)
    break_s = _parse_time(doctor.break_start)
    break_e = _parse_time(doctor.break_end)
    step = doctor.treatment_time or 30  # minutes

    start_dt = datetime.combine(target_date, start_t)
    end_dt = datetime.combine(target_date, end_t)

    # Existing appointments for this doctor+date
    day_start = datetime.combine(target_date, time(0, 0))
    day_end = datetime.combine(target_date, time(23, 59, 59))
    booked_times = {
        a.scheduled_at
        for a in db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.scheduled_at >= day_start,
            Appointment.scheduled_at <= day_end,
            Appointment.status != AppointmentStatus.cancelled,
        ).all()
    }

    slots: List[datetime] = []
    current = start_dt
    while current < end_dt:
        slot_time = current.time()
        # Skip break window
        in_break = (
            break_s and break_e
            and break_s <= slot_time < break_e
        )
        if not in_break and current not in booked_times:
            slots.append(current)
        current += timedelta(minutes=step)

    return slots


def validate_slot(
    db: Session,
    doctor: Doctor,
    scheduled_at: datetime,
) -> Optional[str]:
    """
    Returns error message if the slot is invalid, else None.
    """
    target_date = scheduled_at.date()
    if not _is_doctor_available_on_date(doctor, target_date):
        return "Doctor is not available on the selected date."

    start_t = _parse_time(doctor.working_hours_start) or time(8, 0)
    end_t = _parse_time(doctor.working_hours_end) or time(17, 0)
    slot_time = scheduled_at.time()

    if not (start_t <= slot_time < end_t):
        return f"Outside working hours ({start_t.strftime('%H:%M')}–{end_t.strftime('%H:%M')})."

    break_s = _parse_time(doctor.break_start)
    break_e = _parse_time(doctor.break_end)
    if break_s and break_e and break_s <= slot_time < break_e:
        return f"Slot falls within doctor's break ({break_s.strftime('%H:%M')}–{break_e.strftime('%H:%M')})."

    # Check double-booking
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.scheduled_at == scheduled_at,
        Appointment.status != AppointmentStatus.cancelled,
    ).first()
    if conflict:
        return "This time slot is already booked."

    return None
