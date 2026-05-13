"""Medicines router — search, list, add medicines."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Medicine

router = APIRouter(prefix="/api/medicines", tags=["Medicines"])


class MedicineResponse(BaseModel):
    id: int
    name: str
    generic_name: Optional[str]
    category: Optional[str]
    form: Optional[str]
    strength: Optional[str]

    class Config:
        from_attributes = True


class MedicineCreate(BaseModel):
    name: str
    generic_name: Optional[str] = None
    category: Optional[str] = None
    form: Optional[str] = None
    strength: Optional[str] = None


@router.get("/", response_model=List[MedicineResponse])
def search_medicines(
    q: Optional[str] = Query(None, description="Search term for medicine name"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Medicine).filter(Medicine.is_active == True)
    if q:
        search = f"%{q}%"
        query = query.filter(Medicine.name.ilike(search))
    return query.order_by(Medicine.name).limit(limit).all()


@router.post("/", response_model=MedicineResponse)
def create_medicine(
    data: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Medicine).filter(Medicine.name.ilike(data.name.strip())).first()
    if existing:
        return existing

    medicine = Medicine(**data.model_dump())
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine
