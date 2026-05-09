# MediSys — Hospital Management System

A full-stack hospital management system built with **Python + FastAPI + PostgreSQL + HTMX + Tailwind CSS**.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend + API | FastAPI 0.115 |
| Templating | Jinja2 + HTMX 2 |
| CSS | Tailwind CSS (CDN) |
| Database | PostgreSQL 16 + SQLAlchemy 2 |
| Auth | JWT (python-jose) + bcrypt |
| PDF | ReportLab |
| AI Chat | Google Gemini API (+ fallback) |
| Edge | Cloudflare Worker |
| Container | Docker + Docker Compose |

## Quick Start

### 1. Prerequisites
- Python 3.12+
- PostgreSQL 16 (or Docker)

### 2. Setup environment
```bash
cp .env.example .env
# Edit .env with your DB credentials and secrets
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start PostgreSQL (via Docker)
```bash
docker compose up db -d
```

### 5. Run migrations and seed
```bash
python seed.py
```

### 6. Start the server
```bash
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/login`

## Demo Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@1234` |
| Doctor | `dr_smith` | `Doctor@1234` |
| Doctor | `dr_ali` | `Doctor@1234` |
| Nurse | `nurse_maya` | `Nurse@1234` |
| Pharmacy | `pharmacy1` | `Pharma@1234` |
| Laboratory | `biolab` | `Lab@1234` |

**Demo NFC UID:** `DEMO_NFC_UID_001` → Patient: John Doe

## Project Structure

```
app/
├── main.py           # FastAPI app factory
├── config.py         # Settings
├── database.py       # SQLAlchemy engine
├── dependencies.py   # Auth guards
├── models/           # ORM models (all entities)
├── schemas/          # Pydantic schemas
├── routers/          # API endpoints
│   ├── auth.py       # Login, NFC, logout
│   ├── public.py     # Booking, chat, contact
│   ├── appointments.py
│   ├── patients.py
│   ├── medical_records.py
│   ├── ordonnances.py
│   ├── lab_results.py
│   ├── admin.py
│   └── health.py
├── services/
│   ├── fraud.py      # Fraud detection engine
│   ├── booking.py    # Slot logic
│   ├── ai_chat.py    # Gemini + fallback
│   ├── pdf.py        # ReportLab PDF
│   └── storage.py    # File I/O
├── web.py            # HTMX web views router
└── templates/        # Jinja2 templates
edge/
└── worker.js         # Cloudflare Worker
```

## API Documentation

After starting, visit:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

## Key API Endpoints

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/login` | Staff login → JWT token |
| POST | `/api/nfc-login` | Patient NFC login → JWT token |
| POST | `/api/logout` | Revoke token |

### Public
| Method | Path | Description |
|---|---|---|
| GET | `/api/public/doctors` | List doctors for booking |
| GET | `/api/public/available-slots?doctor_id=&date=` | Available time slots |
| POST | `/api/public/book-appointment` | Guest appointment booking |
| POST | `/api/public/contact` | Contact form |
| POST | `/api/public/medical-chat` | AI medical chat |

### Patients
| Method | Path | Description |
|---|---|---|
| GET | `/api/patients/` | List patients |
| POST | `/api/patients/` | Create patient |
| GET | `/api/patients/{id}` | Get patient |
| PATCH | `/api/patients/{id}` | Update patient |
| GET | `/api/patients/{id}/history` | Full medical history |
| GET | `/api/patients/{id}/recommendations` | AI-free recommendations |
| POST | `/api/patients/{id}/photo` | Upload patient photo |

### Appointments
`GET/POST /api/appointments/` · `GET/PATCH/DELETE /api/appointments/{id}`

### Medical Records
`GET/POST /api/medical-records` · `GET/PATCH/DELETE /api/medical-records/{id}`

### Vitals & Nurse Notes
`POST /api/vitals` · `GET /api/vitals/{patient_id}`
`POST /api/nurse-notes` · `GET /api/nurse-notes/{patient_id}`

### Ordonnances
`GET/POST /api/ordonnances/` · `GET/PATCH/DELETE /api/ordonnances/{id}`
`POST /api/ordonnances/{id}/pdf` · `GET /api/ordonnances/{id}/download-pdf`
`POST /api/ordonnances/{id}/dispense` · `PATCH /api/ordonnances/{id}/toggle-taken`

### Lab Results
`GET /api/lab-results/` · `POST /api/lab-results/upload` · `DELETE /api/lab-results/{id}`

### Admin
`GET/POST /api/admin/users` · `PATCH/DELETE /api/admin/users/{id}`
`GET/PATCH/DELETE /api/admin/messages`
`GET /api/admin/fraud-attempts`
`GET /api/admin/alerts` · `PATCH /api/admin/alerts/{id}/read`

## Fraud Detection

Scoring rules for guest bookings:

| Rule | Score |
|---|---|
| >5 bookings from same IP in 1h | +40 |
| Duplicate phone/email in 2h | +35 |
| Temporary email domain | +25 |
| Suspicious phone pattern | +25 |

Risk levels: `minimal (<10)` · `low (≥10)` · `medium (≥20)` · `high (≥30)` · `critical (≥50)`

## Edge Worker (Cloudflare)

Deploy:
```bash
cd edge
npm install -g wrangler
wrangler deploy
```

Set the `BACKEND_ORIGIN` environment variable to your backend URL.

## Running Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `APP_SECRET_KEY` | App secret (sessions) | — |
| `JWT_SECRET` | JWT signing secret | — |
| `JWT_EXPIRE_MINUTES` | Token lifetime | `480` |
| `UPLOAD_DIR` | Upload directory path | `./uploads` |
| `MAX_UPLOAD_SIZE_MB` | Max file upload size | `10` |
| `GEMINI_API_KEY` | Google Gemini API key (optional) | `""` → fallback |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash` |
| `BACKEND_ORIGIN` | Backend URL for edge worker | — |
| `APP_URL` | Public app URL (for file URLs) | `http://localhost:8000` |

## Docker (Full Stack)

```bash
docker compose up --build
```

This starts PostgreSQL + FastAPI app. Then seed:
```bash
docker compose exec app python seed.py
```
