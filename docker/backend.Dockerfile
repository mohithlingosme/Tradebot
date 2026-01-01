FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Ensure the DB wait helper is executable so entrypoint does not fail
RUN chmod +x scripts/wait-for-db.sh

EXPOSE 8000
CMD ["./scripts/wait-for-db.sh", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
