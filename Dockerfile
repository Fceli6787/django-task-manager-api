# General: API + Web Django (Opción A) — no atado a ningún PC.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Deps sistema para mysqlclient + Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/prod.txt ./requirements/
RUN pip install --upgrade pip setuptools==68.0.0 \
 && pip install -r requirements/prod.txt

COPY . .

RUN mkdir -p /app/logs /app/media /app/staticfiles \
 && python manage.py collectstatic --noinput || true

# No root en prod
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/admin/login/?next=/admin/')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "config.wsgi:application"]
