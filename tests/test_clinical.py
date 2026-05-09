"""Extended acceptance tests — appointments, medical records, ordonnances, lab results."""
from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_medisys_ext.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="session")
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os
    try:
        os.unlink("test_medisys_ext.db")
    except (PermissionError, FileNotFoundError):
        pass


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_token(client):
    from passlib.context import CryptContext
    from app.models import User
    db = TestingSession()
    existing = db.query(User).filter(User.email == "extadmin@test.com").first()
    if not existing:
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        u = User(name="Ext Admin", email="extadmin@test.com", username="extadmin",
                 password_hash=pwd.hash("Admin@1234"), role="admin")
        db.add(u)
        db.commit()
    db.close()
    res = client.post("/api/login", json={"username": "extadmin", "password": "Admin@1234"})
    return res.json()["token"]


@pytest.fixture(scope="session")
def auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def doctor_id(client, auth):
    """Create a doctor user and return doctor profile id."""
    from app.models import User, Doctor
    from passlib.context import CryptContext
    db = TestingSession()
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    u = User(name="Dr. Test", email="drtest@test.com", username="drtest",
             password_hash=pwd.hash("Admin@1234"), role="doctor")
    db.add(u)
    db.flush()
    d = Doctor(
        user_id=u.id,
        specialty="General",
        working_days="Mon,Tue,Wed,Thu,Fri",
        working_hours_start="08:00",
        working_hours_end="17:00",
        treatment_time=30,
    )
    db.add(d)
    db.commit()
    did = d.id
    db.close()
    return did


@pytest.fixture(scope="session")
def patient_id(client, auth):
    """Create a patient and return its id."""
    r = client.post("/api/patients/",
                    json={"name": "Jane Smith", "phone": "+1 555-1234"},
                    headers=auth)
    assert r.status_code == 201
    return r.json()["data"]["id"]


# ── Appointments ──────────────────────────────────────────────────

def test_create_appointment(client, auth, patient_id, doctor_id):
    r = client.post("/api/appointments/", json={
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "scheduled_at": "2027-06-10T09:00:00",
        "reason": "Routine check",
    }, headers=auth)
    assert r.status_code == 201
    assert r.json()["data"]["patient_id"] == patient_id


def test_list_appointments(client, auth):
    r = client.get("/api/appointments/", headers=auth)
    assert r.status_code == 200
    assert r.json()["success"]


def test_update_appointment_status(client, auth, patient_id, doctor_id):
    # Create one
    r = client.post("/api/appointments/", json={
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "scheduled_at": "2027-06-11T10:00:00",
    }, headers=auth)
    appt_id = r.json()["data"]["id"]
    # Update status
    r2 = client.patch(f"/api/appointments/{appt_id}", json={"status": "confirmed"}, headers=auth)
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "confirmed"


# ── Medical Records ───────────────────────────────────────────────

def test_create_medical_record(client, auth, patient_id, doctor_id):
    r = client.post("/api/medical-records", json={
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "diagnosis": "Hypertension",
        "visit_date": "2027-06-10",
        "visit_type": "follow-up",
        "blood_pressure": "140/90",
        "heart_rate": 88,
        "temperature": 37.1,
    }, headers=auth)
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["diagnosis"] == "Hypertension"


def test_list_medical_records(client, auth, patient_id):
    r = client.get(f"/api/medical-records?patient_id={patient_id}", headers=auth)
    assert r.status_code == 200
    assert r.json()["success"]
    assert len(r.json()["data"]) >= 1


# ── Vitals ────────────────────────────────────────────────────────

def test_record_vitals(client, auth, patient_id):
    r = client.post("/api/vitals", json={
        "patient_id": patient_id,
        "temperature": 36.8,
        "blood_pressure": "120/80",
        "heart_rate": 72,
        "oxygen_saturation": 98.5,
    }, headers=auth)
    assert r.status_code == 201


def test_get_patient_vitals(client, auth, patient_id):
    r = client.get(f"/api/vitals/{patient_id}", headers=auth)
    assert r.status_code == 200
    assert r.json()["success"]


# ── Ordonnances ───────────────────────────────────────────────────

def test_create_ordonnance(client, auth, patient_id, doctor_id):
    r = client.post("/api/ordonnances/", json={
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "issued_date": "2027-06-10",
        "medications": [
            {"name": "Amlodipine", "dose": "5mg", "frequency": "Once daily", "duration": "30 days"}
        ],
        "instructions": "Take with food",
    }, headers=auth)
    assert r.status_code == 201
    assert r.json()["data"]["status"] == "active"


def test_list_ordonnances(client, auth):
    r = client.get("/api/ordonnances/", headers=auth)
    assert r.status_code == 200
    assert r.json()["success"]


def test_toggle_taken(client, auth, patient_id, doctor_id):
    r = client.post("/api/ordonnances/", json={
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "issued_date": "2027-06-11",
        "medications": [{"name": "Paracetamol", "dose": "500mg", "frequency": "Three times daily", "duration": "5 days"}],
    }, headers=auth)
    oid = r.json()["data"]["id"]
    r2 = client.patch(f"/api/ordonnances/{oid}/toggle-taken", headers=auth)
    assert r2.status_code == 200
    assert r2.json()["data"]["is_taken"] is True


# ── Patient history ───────────────────────────────────────────────

def test_patient_history(client, auth, patient_id):
    r = client.get(f"/api/patients/{patient_id}/history", headers=auth)
    assert r.status_code == 200
    d = r.json()["data"]
    assert "medical_records" in d
    assert "ordonnances" in d
    assert "vitals_trend" in d


def test_patient_recommendations(client, auth, patient_id):
    r = client.get(f"/api/patients/{patient_id}/recommendations", headers=auth)
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


# ── Available slots ───────────────────────────────────────────────

def test_available_slots(client, doctor_id):
    r = client.get(f"/api/public/available-slots?doctor_id={doctor_id}&date=2027-06-16")
    assert r.status_code == 200
    assert r.json()["success"]


# ── Web UI pages ──────────────────────────────────────────────────

def test_login_page(client):
    r = client.get("/login", follow_redirects=True)
    assert r.status_code == 200
    assert b"MediSys" in r.content


def test_dashboard_page(client):
    r = client.get("/dashboard")
    assert r.status_code == 200


def test_patients_page(client):
    r = client.get("/patients")
    assert r.status_code == 200


def test_admin_page(client):
    r = client.get("/admin")
    assert r.status_code == 200


def test_booking_page(client):
    r = client.get("/booking")
    assert r.status_code == 200
