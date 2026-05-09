"""Database seed script — creates demo users, doctors, patients, and one NFC patient."""
from __future__ import annotations

import sys
from datetime import date

import bcrypt as _bcrypt
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, ".")

from app.database import SessionLocal, Base, engine
from app.models import (
    User, Doctor, Pharmacy, Laboratory, Patient, Appointment,
    MedicalRecord, Ordonnance, VitalSign, NurseNote, Alert,
)

def _hash(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()


def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        if db.query(User).count() > 0:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # ── Users ──────────────────────────────────────────────────────
        admin = User(name="Dr. Admin", email="admin@medisys.com", username="admin",
                     password_hash=_hash("Admin@1234"), role="admin")
        dr_smith = User(name="Dr. Sarah Smith", email="smith@medisys.com", username="dr_smith",
                        password_hash=_hash("Doctor@1234"), role="doctor")
        dr_ali = User(name="Dr. Karim Ali", email="ali@medisys.com", username="dr_ali",
                      password_hash=_hash("Doctor@1234"), role="doctor")
        nurse_maya = User(name="Maya Johnson", email="nurse@medisys.com", username="nurse_maya",
                          password_hash=_hash("Nurse@1234"), role="nurse")
        pharmacy_user = User(name="City Pharmacy", email="pharmacy@medisys.com", username="pharmacy1",
                             password_hash=_hash("Pharma@1234"), role="pharmacy")
        lab_user = User(name="BioLab", email="lab@medisys.com", username="biolab",
                        password_hash=_hash("Lab@1234"), role="laboratory")

        db.add_all([admin, dr_smith, dr_ali, nurse_maya, pharmacy_user, lab_user])
        db.flush()

        # ── Doctors ────────────────────────────────────────────────────
        doc1 = Doctor(user_id=dr_smith.id, specialty="Cardiology", phone="+1 555-0100",
                      license_number="LIC-001", bio="Board-certified cardiologist with 15 years experience.",
                      working_days="Mon,Tue,Wed,Thu,Fri", working_hours_start="08:00",
                      working_hours_end="17:00", break_start="12:00", break_end="13:00",
                      treatment_time=30, clinic_address="123 Medical Drive, Suite 10")
        doc2 = Doctor(user_id=dr_ali.id, specialty="General Practice", phone="+1 555-0200",
                      license_number="LIC-002", bio="Family medicine physician specializing in preventive care.",
                      working_days="Mon,Tue,Wed,Thu,Fri,Sat", working_hours_start="09:00",
                      working_hours_end="18:00", break_start="13:00", break_end="14:00",
                      treatment_time=20, clinic_address="456 Health Ave, Floor 2")
        db.add_all([doc1, doc2])

        # ── Pharmacy & Lab ─────────────────────────────────────────────
        pharmacy = Pharmacy(user_id=pharmacy_user.id, name="City Pharmacy",
                            address="789 Main St", phone="+1 555-0300", license_number="PHAR-001")
        lab = Laboratory(user_id=lab_user.id, name="BioLab Diagnostics",
                         address="101 Lab Way", phone="+1 555-0400", license_number="LAB-001")
        db.add_all([pharmacy, lab])

        # ── Patients ──────────────────────────────────────────────────
        p1 = Patient(name="John Doe", age=45, gender="Male", phone="+1 555-1001",
                     email="john.doe@example.com", blood_type="O+",
                     allergies="Penicillin", date_of_birth=date(1979, 3, 15),
                     address="22 Pine Street", emergency_contact="Jane Doe: +1 555-1002",
                     nfc_uid="DEMO_NFC_UID_001")  # ← demo NFC card
        p2 = Patient(name="Marie Curie", age=38, gender="Female", phone="+1 555-2001",
                     email="mcurie@example.com", blood_type="A+",
                     date_of_birth=date(1986, 7, 22), address="33 Science Blvd")
        p3 = Patient(name="Omar Hassan", age=60, gender="Male", phone="+1 555-3001",
                     email="ohassan@example.com", blood_type="B-",
                     allergies="Aspirin, NSAIDs", date_of_birth=date(1964, 11, 8),
                     address="17 Central Ave")
        db.add_all([p1, p2, p3])
        db.flush()

        # ── Appointments ──────────────────────────────────────────────
        from datetime import datetime
        appt1 = Appointment(
            patient_id=p1.id, doctor_id=doc1.id,
            scheduled_at=datetime(2026, 5, 10, 9, 0),
            reason="Annual cardiac check-up", status="confirmed",
        )
        appt2 = Appointment(
            doctor_id=doc2.id, scheduled_at=datetime(2026, 5, 10, 10, 0),
            reason="Headaches and fatigue", status="pending",
            guest_name="Alice Wonder", guest_phone="+1 555-9999",
            booking_ip="192.168.1.1",
        )
        db.add_all([appt1, appt2])

        # ── Medical Records ───────────────────────────────────────────
        record1 = MedicalRecord(
            patient_id=p1.id, doctor_id=doc1.id,
            diagnosis="Hypertension, Stage 1",
            notes="Patient advised lifestyle changes, low-sodium diet, 30min daily exercise.",
            visit_type="Follow-up", visit_date=date(2026, 4, 15),
            temperature=37.1, blood_pressure="145/90", heart_rate=78,
            weight=82.5, height=175.0,
        )
        db.add(record1)
        db.flush()

        # ── Ordonnances ───────────────────────────────────────────────
        prescription = Ordonnance(
            medical_record_id=record1.id, patient_id=p1.id, doctor_id=doc1.id,
            medications=[
                {"name": "Lisinopril", "dose": "10mg", "frequency": "Once daily", "duration": "90 days"},
                {"name": "Aspirin", "dose": "81mg", "frequency": "Once daily", "duration": "Ongoing"},
            ],
            instructions="Take Lisinopril in the morning with food. Avoid grapefruit.",
            issued_date=date(2026, 4, 15), valid_until=date(2026, 7, 15),
        )
        db.add(prescription)

        # ── Vitals ────────────────────────────────────────────────────
        vital = VitalSign(
            patient_id=p1.id, recorded_by=nurse_maya.id,
            temperature=37.1, blood_pressure="145/90", heart_rate=78,
            oxygen_saturation=98.5, weight=82.5, height=175.0, glucose=95.0,
        )
        db.add(vital)

        # ── Nurse Notes ───────────────────────────────────────────────
        nurse_note = NurseNote(
            patient_id=p1.id, nurse_id=nurse_maya.id,
            note="Patient appeared anxious. BP reading taken after 5min rest. Patient reports occasional dizziness on standing. Educated on orthostatic hypotension precautions.",
        )
        db.add(nurse_note)

        # ── System Alert ─────────────────────────────────────────────
        alert = Alert(
            title="Demo Environment Active",
            message="This is a seeded demo environment. Demo credentials: admin / Admin@1234",
            level="info",
        )
        db.add(alert)

        db.commit()
        print("[OK] Seed complete!")
        print()
        print("Demo Credentials:")
        print("  Admin:      admin / Admin@1234")
        print("  Doctor:     dr_smith / Doctor@1234")
        print("  Doctor:     dr_ali / Doctor@1234")
        print("  Nurse:      nurse_maya / Nurse@1234")
        print("  Pharmacy:   pharmacy1 / Pharma@1234")
        print("  Laboratory: biolab / Lab@1234")
        print()
        print("Demo NFC UID: DEMO_NFC_UID_001 (maps to patient John Doe)")

    except Exception as e:
        db.rollback()
        print(f"[FAIL] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
