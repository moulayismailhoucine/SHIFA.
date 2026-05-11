FROM python:3.12-slim

WORKDIR /app

# Install system deps including libgomp1 for TensorFlow
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq-dev gcc libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cache bust to ensure fresh code copy
ARG CACHE_BUST=1
COPY . .

# Verify model file exists
RUN ls -la app/ai/models/bone_fracture_model.h5 || echo "WARNING: Model file not found!"

# Create upload dir
RUN mkdir -p uploads/patients uploads/lab_results uploads/ordonnances

EXPOSE 8000

# Run Alembic migrations then start the app
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
