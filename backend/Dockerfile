# ARBOR Backend
# Python 3.11 + FastAPI
FROM python:3.11-slim AS base

# Empêcher la génération de fichiers .pyc et forcer le flush stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances système pour psycopg2 et lxml
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        libxml2-dev \
        libxslt1-dev && \
    rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copier le code source
COPY . .

# Créer le répertoire de stockage BOM
RUN mkdir -p /data/bom_storage

# Port par défaut
EXPOSE 8000

# Lancement via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
