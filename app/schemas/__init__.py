"""Pydantic request/response schemas."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ─────────────────────────────────────────────────────────────────
# Shared
# ─────────────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = ""


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────

class StaffLoginRequest(BaseModel):
    username: str = Field(..., min_length=2)
    password: str = Field(..., min_length=6)


class NfcLoginRequest(BaseModel):
    nfc_uid: str = Field(..., min_length=4, max_length=100)


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: Optional[Dict[str, Any]] = None
    patient: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    role: str = "doctor"
    is_active: bool = True
    # Nurse profile fields
    doctor_id: Optional[int] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    shift: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    # Nurse profile fields
    doctor_id: Optional[int] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    shift: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    username: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────
# Patients
# ─────────────────────────────────────────────────────────────────

PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=2)
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    emergency_contact: Optional[str] = None
    nfc_uid: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not PHONE_RE.match(v):
            raise ValueError("Invalid phone format")
        return v


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    emergency_contact: Optional[str] = None
    nfc_uid: Optional[str] = None
    is_active: Optional[bool] = None


class PatientOut(BaseModel):
    id: int
    name: str
    age: Optional[int]
    gender: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    blood_type: Optional[str]
    allergies: Optional[str]
    address: Optional[str]
    date_of_birth: Optional[date]
    emergency_contact: Optional[str]
    nfc_uid: Optional[str]
    is_active: bool
    photo: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────
# Doctors
# ─────────────────────────────────────────────────────────────────

class DoctorCreate(BaseModel):
    user_id: int
    specialty: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    bio: Optional[str] = None
    working_days: Optional[str] = "Mon,Tue,Wed,Thu,Fri"
    working_hours_start: Optional[str] = "08:00"
    working_hours_end: Optional[str] = "17:00"
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    treatment_time: int = 30
    clinic_address: Optional[str] = None


class DoctorUpdate(BaseModel):
    specialty: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    working_days: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    treatment_time: Optional[int] = None
    clinic_address: Optional[str] = None


class DoctorOut(BaseModel):
    id: int
    user_id: int
    specialty: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    working_days: Optional[str]
    working_hours_start: Optional[str]
    working_hours_end: Optional[str]
    break_start: Optional[str]
    break_end: Optional[str]
    treatment_time: int
    clinic_address: Optional[str]
    avatar: Optional[str]
    user: Optional[UserOut] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────
# Appointments
# ─────────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: int
    scheduled_at: datetime
    reason: Optional[str] = None
    notes: Optional[str] = None
    # Guest fields
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_email: Optional[str] = None
    # Public user tracking
    device_id: Optional[str] = None
    # Anti-bot honeypot
    website: Optional[str] = None
    confirm_email: Optional[str] = None

    @field_validator("guest_phone")
    @classmethod
    def validate_guest_phone(cls, v):
        if v and not PHONE_RE.match(v):
            raise ValueError("Invalid phone format")
        return v


class AppointmentUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AppointmentOut(BaseModel):
    id: int
    patient_id: Optional[int]
    doctor_id: int
    scheduled_at: datetime
    reason: Optional[str]
    status: str
    notes: Optional[str]
    guest_name: Optional[str]
    guest_phone: Optional[str]
    device_id: Optional[str]
    is_suspicious: bool
    fraud_score: int
    fraud_risk_level: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────
# Medical Records
# ─────────────────────────────────────────────────────────────────

class MedicalRecordCreate(BaseModel):
    patient_id: int
    doctor_id: int
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    visit_type: Optional[str] = None
    visit_date: date
    temperature: Optional[float] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None


class MedicalRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    visit_type: Optional[str] = None
    temperature: Optional[float] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None


class MedicalRecordOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    diagnosis: Optional[str]
    notes: Optional[str]
    visit_type: Optional[str]
    visit_date: date
    temperature: Optional[float]
    blood_pressure: Optional[str]
    heart_rate: Optional[int]
    weight: Optional[float]
    height: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────
# Ordonnances
# ─────────────────────────────────────────────────────────────────

class MedicationItem(BaseModel):
    name: str
    dose: str
    frequency: str
    duration: str
    method: Optional[str] = "oral"
    note: Optional[str] = None


class OrdonnanceCreate(BaseModel):
    medical_record_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    medications: List[MedicationItem] = []
    instructions: Optional[str] = None
    issued_date: date
    valid_until: Optional[date] = None


class OrdonnanceUpdate(BaseModel):
    medications: Optional[List[MedicationItem]] = None
    instructions: Optional[str] = None
    valid_until: Optional[date] = None
    status: Optional[str] = None
    is_taken: Optional[bool] = None


class OrdonnanceOut(BaseModel):
    id: int
    reference_number: Optional[str] = None
    patient_id: int
    doctor_id: int
    medications: Optional[Any]
    instructions: Optional[str]
    issued_date: date
    valid_until: Optional[date]
    status: str
    is_taken: bool
    pdf_path: Optional[str]
    dispensed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────
# Lab Results
# ─────────────────────────────────────────────────────────────────

class LabResultCreate(BaseModel):
    patient_id: int
    laboratory_id: Optional[int] = None
    title: str
    category: Optional[str] = None  # xray | mri | ct_scan | ultrasound | blood_test | other
    note: Optional[str] = None


class LabResultOut(BaseModel):
    id: int
    patient_id: int
    laboratory_id: Optional[int]
    title: str
    file_path: Optional[str]
    file_type: Optional[str]
    category: Optional[str]
    note: Optional[str]
    created_at: datetime
    # AI analysis
    ai_diagnosis: Optional[str] = None
    ai_probability: Optional[float] = None
    ai_note: Optional[str] = None
    ai_analyzed_at: Optional[datetime] = None
    ai_model_version: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────
# Vitals / Nurse Notes
# ─────────────────────────────────────────────────────────────────

class VitalSignCreate(BaseModel):
    patient_id: int
    temperature: Optional[float] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    glucose: Optional[float] = None
    notes: Optional[str] = None


class VitalSignOut(BaseModel):
    id: int
    patient_id: int
    temperature: Optional[float]
    blood_pressure: Optional[str]
    heart_rate: Optional[int]
    oxygen_saturation: Optional[float]
    weight: Optional[float]
    glucose: Optional[float]
    recorded_at: datetime

    model_config = {"from_attributes": True}


class NurseNoteCreate(BaseModel):
    patient_id: int
    note: str = Field(..., min_length=5)


class NurseNoteOut(BaseModel):
    id: int
    patient_id: int
    nurse_id: int
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool = True
    reply: str
    provider: str  # "gemini" | "fallback"
    disclaimer: str = (
        "This is an AI assistant. It does not provide medical diagnoses. "
        "Always consult a qualified healthcare professional."
    )


# ─────────────────────────────────────────────────────────────────
# Contact
# ─────────────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    subject: Optional[str] = None
    message: str = Field(..., min_length=10)
    # Honeypot
    website: Optional[str] = None


# ─────────────────────────────────────────────────────────────────
# Public booking
# ─────────────────────────────────────────────────────────────────

class PublicBookingRequest(BaseModel):
    doctor_id: int
    scheduled_at: datetime
    guest_name: str = Field(..., min_length=2, max_length=255)
    guest_phone: str = Field(..., min_length=7, max_length=30)
    guest_email: Optional[str] = None
    reason: Optional[str] = None
    device_id: Optional[str] = None
    # Honeypot fields
    website: Optional[str] = None
    confirm_email: Optional[str] = None

    @field_validator("guest_phone")
    @classmethod
    def validate_phone(cls, v):
        if not PHONE_RE.match(v):
            raise ValueError("Invalid phone format")
        return v
