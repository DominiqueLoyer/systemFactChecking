# SysCRED Docker Configuration for Render
# Build context: 02_Code/
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (light version for Render free tier)
COPY syscred/requirements-light.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn psycopg2-binary flask_sqlalchemy

# Copy everything from 02_Code/
COPY . /app

EXPOSE 10000

# Run gunicorn with PORT from Render (defaults to 10000)
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 syscred.backend_app:app
