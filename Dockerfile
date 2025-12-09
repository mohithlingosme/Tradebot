# Use official Python image
FROM python:3.12-slim

# Create app directory
WORKDIR /app

# Install system deps if ever needed (left simple for now)
# RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY requirements.txt requirements-indicators.txt requirements-core.txt requirements-dev.txt requirements-trading.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose API port
EXPOSE 8000

# Default command to start API
# This matches how you ran it before: python -m market_data_ingestion.src.api
CMD ["python", "-m", "market_data_ingestion.src.api"]
