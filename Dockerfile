# ========== Stage: Base ==========
# FROM python:3.10-slim AS base
FROM python:3.12 AS base

# Set workdir
WORKDIR /app

# Copy dan install dependencies tanpa cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code dan static assets
COPY api/    ./api/
COPY js/     ./js/
COPY css/    ./css/
COPY images/    ./images/
COPY sections/   ./sections/
COPY index.html .

# Ekspos port
EXPOSE 5004 5001 5002 5003 8000

# ======== Entrypoint: jalankan semua service ========
# - Uvicorn masing-masing app FastAPI di background
# - Terakhir, serve static/index via built-in http.server
CMD \
  uvicorn api.chatbot.main:app --host 0.0.0.0 --port 5000 --log-level info & \
  uvicorn api.get_data.main:app --host 0.0.0.0 --port 5001 --log-level info & \
  uvicorn api.forecasting.main:app --host 0.0.0.0 --port 5002 --log-level info & \
  uvicorn models.clustering.clustering.main:app --host 0.0.0.0 --port 5003 --log-level info & \
  python -m http.server 8000 --directory .