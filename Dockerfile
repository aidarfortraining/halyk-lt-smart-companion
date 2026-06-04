# ── Stage 1: build the React SPA ──
FROM node:24-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build -- --outDir dist --emptyOutDir

# ── Stage 2: Django + Gunicorn runtime (single container) ──
FROM python:3.12-slim AS backend
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DJANGO_DEBUG=0
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend /fe/dist ./frontend_dist
RUN python manage.py collectstatic --noinput

EXPOSE 8000
# migrate + idempotent seed on every start (state lives on the volume), then serve.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_demo && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
