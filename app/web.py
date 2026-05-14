"""Web UI router — HTMX-powered Jinja2 views."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app.i18n import get_lang, is_rtl, translator

router = APIRouter(tags=["Web UI"])

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Inject i18n helpers into every Jinja2 template
def _t(text: str) -> str:
    # This closure is replaced per-request below, but exists as a fallback
    return text

# We'll use a before-request style injection via a custom render helper
def _render(request: Request, name: str, ctx: dict = None):
    lang = get_lang(request)
    ctx = ctx or {}
    ctx["_lang"] = lang
    ctx["_rtl"] = is_rtl(lang)
    ctx["_"] = lambda text: translator(text, lang)
    return templates.TemplateResponse(request, name, ctx)


@router.get("/set-lang/{lang}")
def set_lang(lang: str, request: Request):
    """Set language cookie and redirect back."""
    if lang not in ("en", "fr", "ar"):
        lang = "en"
    redirect_url = request.headers.get("referer", "/dashboard")
    resp = RedirectResponse(url=redirect_url, status_code=302)
    resp.set_cookie(key="lang", value=lang, max_age=31536000, path="/")
    return resp


@router.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return RedirectResponse(url="/login")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return _render(request, "login.html")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return _render(request, "dashboard/index.html")


@router.get("/pharmacy", response_class=HTMLResponse)
def pharmacy_dashboard(request: Request):
    return _render(request, "pharmacy/dashboard.html")


@router.get("/patients", response_class=HTMLResponse)
def patients_page(request: Request):
    return _render(request, "patients/index.html")


@router.get("/patients/{patient_id}", response_class=HTMLResponse)
def patient_detail_page(request: Request, patient_id: int):
    return _render(request, "patients/detail.html", {"patient_id": patient_id})


@router.get("/appointments", response_class=HTMLResponse)
def appointments_page(request: Request):
    return _render(request, "appointments/index.html")


@router.get("/medical-records", response_class=HTMLResponse)
def medical_records_page(request: Request):
    return _render(request, "medical_records/index.html")


@router.get("/ordonnances", response_class=HTMLResponse)
def ordonnances_page(request: Request):
    return _render(request, "ordonnances/index.html")


@router.get("/lab-results", response_class=HTMLResponse)
def lab_results_page(request: Request):
    return _render(request, "lab_results/index.html")


@router.get("/lab", response_class=HTMLResponse)
def lab_dashboard(request: Request):
    return _render(request, "lab/index.html")


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return _render(request, "admin/index.html")


@router.get("/admin/doctors", response_class=HTMLResponse)
def admin_doctors_page(request: Request):
    return _render(request, "admin/doctors.html")


@router.get("/admin/nurses", response_class=HTMLResponse)
def admin_nurses_page(request: Request):
    return _render(request, "admin/nurses.html")


@router.get("/admin/laboratories", response_class=HTMLResponse)
def admin_laboratories_page(request: Request):
    return _render(request, "admin/laboratories.html")


@router.get("/nurse/orders", response_class=HTMLResponse)
def nurse_orders_page(request: Request):
    return _render(request, "nursing/orders.html")


@router.get("/nurse/vitals", response_class=HTMLResponse)
def nurse_vitals_page(request: Request):
    return _render(request, "nursing/vitals.html")


@router.get("/nurse/notes", response_class=HTMLResponse)
def nurse_notes_page(request: Request):
    return _render(request, "nursing/notes.html")


@router.get("/booking", response_class=HTMLResponse)
def public_booking(request: Request):
    return _render(request, "public/booking.html")


@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return _render(request, "public/chat.html")


@router.get("/contact", response_class=HTMLResponse)
def contact_page(request: Request):
    return _render(request, "public/contact.html")
