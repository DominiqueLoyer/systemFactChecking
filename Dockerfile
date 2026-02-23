# SysCRED Docker Configuration for Render (Lite)
# Version allégée pour respecter le quota de 528MB
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV SYSCRED_LOAD_ML_MODELS=false
ENV SYSCRED_ENV=production

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy lite requirements
COPY requirements-lite.txt /app/requirements.txt

# Install dependencies (no heavy ML models)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY syscred/ /app/syscred/
COPY ontology/ /app/ontology/

# Create user for security
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

WORKDIR /app

# Render uses PORT env variable
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "syscred.backend_app:app"]
