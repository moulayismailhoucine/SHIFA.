"""Healthcheck router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }

@router.get("/setup-admin-secret")
def setup_admin(db: Session = Depends(get_db)):
    """Temporary endpoint to create a default admin. Remove after use!"""
    import bcrypt
    from app.models import User
    
    existing = db.query(User).filter_by(username="admin").first()
    if existing:
        return {"status": "error", "message": "Admin already exists! You can log in with username 'admin'."}
        
    hashed = bcrypt.hashpw("Admin@1234".encode(), bcrypt.gensalt()).decode()
    new_admin = User(
        name="Super Admin",
        email="admin@myclinic.com",
        username="admin",
        password_hash=hashed,
        role="admin"
    )
    db.add(new_admin)
    db.commit()
    return {"status": "success", "message": "Admin account created! Username: admin | Password: Admin@1234. Please log in and change your password immediately."}

