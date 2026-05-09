"""Basic acceptance tests for the hospital management system."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use SQLite for tests (no PG needed)
TEST_DATABASE_URL = "sqlite:///./test_medisys.db"
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
        os.unlink("test_medisys.db")
    except PermissionError:
        pass  # Windows may keep file locked briefly


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_user(client):
    """Create and authenticate admin user."""
    from passlib.context import CryptContext
    from app.models import User
    db = TestingSession()
    existing = db.query(User).filter(User.email == "testadmin@test.com").first()
    if not existing:
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        u = User(name="Test Admin", email="testadmin@test.com", username="testadmin",
                 password_hash=pwd.hash("Admin@1234"), role="admin")
        db.add(u)
        db.commit()
    db.close()
    res = client.post("/api/login", json={"username": "testadmin", "password": "Admin@1234"})
    return res.json()


@pytest.fixture(scope="session")
def auth_headers(admin_user):
    return {"Authorization": f"Bearer {admin_user['token']}"}


# ── Health ──────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert "status" in r.json()


# ── Auth ────────────────────────────────────────────────────────

def test_staff_login_success(client, admin_user):
    assert admin_user["token"]
    assert admin_user["user"]["role"] == "admin"


def test_staff_login_wrong_password(client):
    r = client.post("/api/login", json={"username": "testadmin", "password": "wrongpass"})
    assert r.status_code == 401


def test_nfc_login_invalid(client):
    r = client.post("/api/nfc-login", json={"nfc_uid": "NONEXISTENT_UID"})
    assert r.status_code == 404


def test_logout(client, admin_user):
    # Get a fresh token (separate from the shared admin session token)
    r = client.post("/api/login", json={"username": "testadmin", "password": "Admin@1234"})
    temp_token = r.json().get("token", "")
    r = client.post("/api/logout", headers={"Authorization": f"Bearer {temp_token}"})
    assert r.status_code == 200


# ── Patients ────────────────────────────────────────────────────

def test_create_patient(client, auth_headers):
    r = client.post("/api/patients/", json={"name": "Test Patient", "phone": "+1 555-0000"}, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["data"]["name"] == "Test Patient"


def test_list_patients(client, auth_headers):
    r = client.get("/api/patients/", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"]


# ── Public booking ──────────────────────────────────────────────

def test_honeypot_rejection(client):
    r = client.post("/api/public/book-appointment", json={
        "doctor_id": 1,
        "scheduled_at": "2026-06-01T10:00:00",
        "guest_name": "Bot",
        "guest_phone": "+1 555-0001",
        "website": "http://spam.com",  # honeypot filled
    })
    assert r.status_code == 403


def test_public_doctors_list(client):
    r = client.get("/api/public/doctors")
    assert r.status_code == 200
    assert r.json()["success"]


def test_available_slots_invalid_date(client):
    r = client.get("/api/public/available-slots?doctor_id=1&date=not-a-date")
    assert r.status_code == 422


# ── AI Chat ─────────────────────────────────────────────────────

def test_ai_chat_fallback(client):
    r = client.post("/api/public/medical-chat", json={"message": "What are symptoms of flu?"})
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert data["provider"] in ("gemini", "fallback")


def test_ai_chat_too_short(client):
    r = client.post("/api/public/medical-chat", json={"message": "h"})
    assert r.status_code == 422


# ── Contact form ─────────────────────────────────────────────────

def test_contact_honeypot(client):
    r = client.post("/api/public/contact", json={
        "name": "Bot", "email": "bot@spam.com",
        "message": "This is a spam message to test honeypot",
        "website": "http://spam.com",
    })
    assert r.status_code == 403


def test_contact_success(client):
    r = client.post("/api/public/contact", json={
        "name": "Real User", "email": "user@example.com",
        "message": "I have a question about appointments",
    })
    assert r.status_code == 201


# ── Admin ────────────────────────────────────────────────────────

def test_admin_list_users(client, auth_headers):
    r = client.get("/api/admin/users", headers=auth_headers)
    assert r.status_code == 200


def test_admin_fraud_attempts(client, auth_headers):
    r = client.get("/api/admin/fraud-attempts", headers=auth_headers)
    assert r.status_code == 200
