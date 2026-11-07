# Production Dockerfile for FoodLens AI
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (barcode, OCR, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libzbar0 \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY . .

# Ensure data directories exist
RUN mkdir -p data/uploads data/models

# Expose Streamlit (8501) and FastAPI (8000)
EXPOSE 8501 8000

# Copy start script
RUN chmod +x start.sh

# Default to running Streamlit UI; can be overridden to run FastAPI or both
CMD ["./start.sh"]
