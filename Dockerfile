# SysCRED Docker Configuration for Render
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/02_Code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file from 02_Code/syscred/
COPY 02_Code/syscred/requirements.txt /app/requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn psycopg2-binary flask_sqlalchemy

# Copy the entire project
COPY . /app

# Expose port
EXPOSE 5000

# Run gunicorn pointing to the correct module path
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--chdir", "/app/02_Code", "syscred.backend_app:app"]
