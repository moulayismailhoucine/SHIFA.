"""SQLAlchemy ORM models — all tables in one module."""

import enum
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text, func, UniqueConstraint, BigInteger,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


# ─────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────

class RoleEnum(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"
    nurse = "nurse"
    pharmacy = "pharmacy"
    laboratory = "laboratory"


class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class FraudRiskLevel(str, enum.Enum):
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ContactStatus(str, enum.Enum):
    new = "new"
    read = "read"
    archived = "archived"


class OrdonnanceStatus(str, enum.Enum):
    active = "active"
    dispensed = "dispensed"
    expired = "expired"
    cancelled = "cancelled"


class NursingOrderStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class NursingOrderPriority(str, enum.Enum):
    routine = "routine"
    urgent = "urgent"
    stat = "stat"


# ─────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.doctor)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    doctor: Mapped[Optional["Doctor"]] = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    pharmacy: Mapped[Optional["Pharmacy"]] = relationship("Pharmacy", back_populates="user", uselist=False, cascade="all, delete-orphan")
    laboratory: Mapped[Optional["Laboratory"]] = relationship("Laboratory", back_populates="user", uselist=False, cascade="all, delete-orphan")
    nurse: Mapped[Optional["Nurse"]] = relationship("Nurse", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tokens: Mapped[List["AuthToken"]] = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    chats: Mapped[List["Chat"]] = relationship("Chat", back_populates="user")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[Optional["User"]] = relationship("User", back_populates="tokens")
    patient: Mapped[Optional["Patient"]] = relationship("Patient", back_populates="tokens")


# ─────────────────────────────────────────────────────────────────
# Patients
# ─────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    nfc_uid: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    blood_type: Mapped[Optional[str]] = mapped_column(String(10))
    allergies: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    photo: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="patient")
    medical_records: Mapped[List["MedicalRecord"]] = relationship("MedicalRecord", back_populates="patient")
    ordonnances: Mapped[List["Ordonnance"]] = relationship("Ordonnance", back_populates="patient")
    lab_results: Mapped[List["LabResult"]] = relationship("LabResult", back_populates="patient")
    vitals: Mapped[List["VitalSign"]] = relationship("VitalSign", back_populates="patient")
    nurse_notes: Mapped[List["NurseNote"]] = relationship("NurseNote", back_populates="patient")
    tokens: Mapped[List["AuthToken"]] = relationship("AuthToken", back_populates="patient")


# ─────────────────────────────────────────────────────────────────
# Doctors
# ─────────────────────────────────────────────────────────────────

class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    specialty: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    working_days: Mapped[Optional[str]] = mapped_column(String(50))   # "Mon,Tue,Wed,Thu,Fri"
    working_hours_start: Mapped[Optional[str]] = mapped_column(String(10))  # "08:00"
    working_hours_end: Mapped[Optional[str]] = mapped_column(String(10))    # "17:00"
    break_start: Mapped[Optional[str]] = mapped_column(String(10))
    break_end: Mapped[Optional[str]] = mapped_column(String(10))
    treatment_time: Mapped[int] = mapped_column(Integer, default=30)   # minutes
    clinic_address: Mapped[Optional[str]] = mapped_column(Text)
    avatar: Mapped[Optional[str]] = mapped_column(String(500))

    user: Mapped["User"] = relationship("User", back_populates="doctor")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="doctor")
    medical_records: Mapped[List["MedicalRecord"]] = relationship("MedicalRecord", back_populates="doctor")
    ordonnances: Mapped[List["Ordonnance"]] = relationship("Ordonnance", back_populates="doctor")
    unavailabilities: Mapped[List["DoctorUnavailability"]] = relationship("DoctorUnavailability", back_populates="doctor")
    nurses: Mapped[List["Nurse"]] = relationship("Nurse", back_populates="doctor")
    nursing_orders: Mapped[List["NursingOrder"]] = relationship("NursingOrder", back_populates="doctor", foreign_keys="NursingOrder.doctor_id")


class DoctorUnavailability(Base):
    __tablename__ = "doctor_unavailabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[Optional[str]] = mapped_column(String(255))

    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="unavailabilities")


# ─────────────────────────────────────────────────────────────────
# Pharmacy / Laboratory
# ─────────────────────────────────────────────────────────────────

class Nurse(Base):
    __tablename__ = "nurses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    doctor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    shift: Mapped[Optional[str]] = mapped_column(String(50))   # "Day", "Night", "Evening"

    user: Mapped["User"] = relationship("User", back_populates="nurse")
    doctor: Mapped[Optional["Doctor"]] = relationship("Doctor", back_populates="nurses")


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    license_number: Mapped[Optional[str]] = mapped_column(String(100))

    user: Mapped["User"] = relationship("User", back_populates="pharmacy")


class Laboratory(Base):
    __tablename__ = "laboratories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    license_number: Mapped[Optional[str]] = mapped_column(String(100))

    user: Mapped["User"] = relationship("User", back_populates="laboratory")
    lab_results: Mapped[List["LabResult"]] = relationship("LabResult", back_populates="laboratory")


# ─────────────────────────────────────────────────────────────────
# Appointments
# ─────────────────────────────────────────────────────────────────

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.pending)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Guest booking fields
    guest_name: Mapped[Optional[str]] = mapped_column(String(255))
    guest_phone: Mapped[Optional[str]] = mapped_column(String(30))
    guest_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Public user tracking (no account needed)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # Fraud detection
    booking_ip: Mapped[Optional[str]] = mapped_column(String(50))
    booking_ua: Mapped[Optional[str]] = mapped_column(String(500))
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    fraud_score: Mapped[int] = mapped_column(Integer, default=0)
    fraud_reason: Mapped[Optional[str]] = mapped_column(Text)
    fraud_risk_level: Mapped[Optional[str]] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped[Optional["Patient"]] = relationship("Patient", back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="appointments")


# ─────────────────────────────────────────────────────────────────
# Medical Records
# ─────────────────────────────────────────────────────────────────

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"))
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    visit_type: Mapped[Optional[str]] = mapped_column(String(50))
    visit_date: Mapped[date] = mapped_column(Date)

    # Vitals embedded
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    blood_pressure: Mapped[Optional[str]] = mapped_column(String(20))
    heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    height: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped["Patient"] = relationship("Patient", back_populates="medical_records")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="medical_records")
    ordonnances: Mapped[List["Ordonnance"]] = relationship("Ordonnance", back_populates="medical_record")


# ─────────────────────────────────────────────────────────────────
# Ordonnances (Prescriptions)
# ─────────────────────────────────────────────────────────────────

class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    generic_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g. analgesic, antibiotic
    form: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # tablet, capsule, syrup, injection
    strength: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 500mg, 250mg/5ml
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Ordonnance(Base):
    __tablename__ = "ordonnances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medical_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("medical_records.id", ondelete="SET NULL"), nullable=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"))
    medications: Mapped[Optional[dict]] = mapped_column(JSON)   # [{name, dose, frequency, duration}]
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    issued_date: Mapped[date] = mapped_column(Date)
    valid_until: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[OrdonnanceStatus] = mapped_column(Enum(OrdonnanceStatus), default=OrdonnanceStatus.active)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    is_taken: Mapped[bool] = mapped_column(Boolean, default=False)
    dispensed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    dispensed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    patient: Mapped["Patient"] = relationship("Patient", back_populates="ordonnances")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="ordonnances")
    medical_record: Mapped[Optional["MedicalRecord"]] = relationship("MedicalRecord", back_populates="ordonnances")


# ─────────────────────────────────────────────────────────────────
# Lab Results
# ─────────────────────────────────────────────────────────────────

class LabResult(Base):
    __tablename__ = "lab_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    laboratory_id: Mapped[Optional[int]] = mapped_column(ForeignKey("laboratories.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # xray | mri | ct_scan | ultrasound | blood_test | other
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # AI X-ray analysis
    ai_diagnosis: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_probability: Mapped[Optional[float]] = mapped_column(nullable=True)
    ai_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ai_model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="lab_results")
    laboratory: Mapped[Optional["Laboratory"]] = relationship("Laboratory", back_populates="lab_results")


# ─────────────────────────────────────────────────────────────────
# Vitals / Nurse Notes
# ─────────────────────────────────────────────────────────────────

class VitalSign(Base):
    __tablename__ = "vital_signs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    recorded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    blood_pressure: Mapped[Optional[str]] = mapped_column(String(20))
    heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    oxygen_saturation: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    height: Mapped[Optional[float]] = mapped_column(Float)
    glucose: Mapped[Optional[float]] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="vitals")


class NurseNote(Base):
    __tablename__ = "nurse_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    nurse_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    patient: Mapped["Patient"] = relationship("Patient", back_populates="nurse_notes")


# ─────────────────────────────────────────────────────────────────
# Nursing Orders
# ─────────────────────────────────────────────────────────────────

class NursingOrder(Base):
    __tablename__ = "nursing_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"))
    nurse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    order_type: Mapped[str] = mapped_column(String(50), default="medication")  # medication | monitoring | care | other
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    medication_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # oral | injection | iv | topical | inhalation | subcutaneous | rectal | other
    priority: Mapped[NursingOrderPriority] = mapped_column(Enum(NursingOrderPriority), default=NursingOrderPriority.routine)
    status: Mapped[NursingOrderStatus] = mapped_column(Enum(NursingOrderStatus), default=NursingOrderStatus.pending)

    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completion_note: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped["Patient"] = relationship("Patient")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="nursing_orders", foreign_keys=[doctor_id])


# ─────────────────────────────────────────────────────────────────
# Chat / AI Audit
# ─────────────────────────────────────────────────────────────────

class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    provider_used: Mapped[Optional[str]] = mapped_column(String(50))  # "gemini" | "fallback"
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[Optional["User"]] = relationship("User", back_populates="chats")


# ─────────────────────────────────────────────────────────────────
# Contact Messages
# ─────────────────────────────────────────────────────────────────

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[ContactStatus] = mapped_column(Enum(ContactStatus), default=ContactStatus.new)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ─────────────────────────────────────────────────────────────────
# Fraud Attempts
# ─────────────────────────────────────────────────────────────────

class FraudAttempt(Base):
    __tablename__ = "fraud_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    payload: Mapped[Optional[dict]] = mapped_column(JSON)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20))
    score: Mapped[int] = mapped_column(Integer, default=0)
    was_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ─────────────────────────────────────────────────────────────────
# Alerts
# ─────────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), default="info")  # info | warning | critical
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
