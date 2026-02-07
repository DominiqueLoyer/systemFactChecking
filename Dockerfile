# SysCRED Docker Configuration for Render (Optimized)
# Reduces image from 4.36GB to ~200MB
# Last Updated: Fix for Render Build Paths (02_Code context)

FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV SYSCRED_LOAD_ML_MODELS=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (cache layer)
# Ensuring we grab the file from the correct source path (requirements.txt exists, light version does not)
COPY 02_Code/syscred/requirements.txt /app/requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary application code
COPY 02_Code/syscred/ /app/syscred/

EXPOSE 5000

# Use PORT env variable from Render
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 syscred.backend_app:app
