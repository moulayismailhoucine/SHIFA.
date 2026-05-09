"""FastAPI application factory."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import Base, engine
from app.routers import (
    auth, public, appointments, patients,
    medical_records, ordonnances, lab_results, admin, health, uploads,
    nursing_orders, doctor, ai,
)

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables (use Alembic for production migrations)
    Base.metadata.create_all(bind=engine)
    # Ensure upload directories exist
    for subdir in ["patients", "lab_results", "ordonnances"]:
        Path(settings.upload_dir, subdir).mkdir(parents=True, exist_ok=True)
    logger.info("MediSys application started")
    yield
    logger.info("MediSys application shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="MediSys — Hospital Management System",
        description="Full hospital management API: patients, appointments, records, ordonnances, lab results, AI chat.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    static_path = Path(__file__).parent / "static"
    static_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(public.router)
    app.include_router(appointments.router)
    app.include_router(patients.router)
    app.include_router(medical_records.router)
    app.include_router(ordonnances.router)
    app.include_router(lab_results.router)
    app.include_router(uploads.router)
    app.include_router(admin.router)
    app.include_router(doctor.router)
    app.include_router(nursing_orders.router)
    app.include_router(ai.router)

    # Web UI routes (HTMX-powered)
    from app.web import router as web_router
    app.include_router(web_router)

    return app


app = create_app()
