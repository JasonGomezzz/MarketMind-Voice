# ============================================================
# MarketMind IA — Backend Dockerfile
# Python 3.11.9 slim — multi-stage para imagen liviana
# ============================================================

FROM python:3.11.9-slim AS base

# Metadata
LABEL maintainer="MarketMind IA Team"
LABEL description="Django REST API for MarketMind IA"

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Dependencias del sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (caché de Docker)
COPY requirements/ requirements/

# Instalar dependencias de producción
RUN pip install --upgrade pip \
    && pip install -r requirements/base.txt

# Copiar el código fuente
COPY . .

# Recopilar archivos estáticos
RUN python manage.py collectstatic --noinput --settings=core.settings.prod || true

# Puerto expuesto
EXPOSE 8000

# Comando por defecto (producción con gunicorn)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120 --access-logfile - --error-logfile - core.wsgi:application"]
