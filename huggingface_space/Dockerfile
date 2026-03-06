# SysCRED Docker Configuration for Hugging Face Spaces
# Full version with PyTorch and Transformers
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV SYSCRED_LOAD_ML_MODELS=true
ENV SYSCRED_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (full version with ML)
COPY requirements.txt /app/requirements.txt

# Install dependencies (includes PyTorch, Transformers)
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models for NER
RUN python -m spacy download en_core_web_md || true
RUN python -m spacy download fr_core_news_md || true

# Copy application code
COPY syscred/ /app/syscred/
COPY ontology/ /app/ontology/
# Crée le dossier instance et donne les droits
RUN mkdir -p /app/instance && chmod 777 /app/instance

# Create user for HF Spaces (required)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

WORKDIR /app

EXPOSE 7860

# Run with HF Spaces port (7860)
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "300", "syscred.backend_app:app"]
