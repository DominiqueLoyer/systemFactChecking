# SysCRED Docker Configuration for Hugging Face Spaces
# OPTIMIZED version with Distilled Models for faster startup
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# ============================================
# KEY OPTIMIZATION: Use distilled models
# ============================================
ENV SYSCRED_LOAD_ML_MODELS=true
ENV SYSCRED_USE_DISTILLED=true
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HOME=/app/.cache/huggingface

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy optimized requirements (distilled models, CPU-only torch)
COPY syscred/requirements-distilled.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# PRE-DOWNLOAD DISTILLED MODELS (Build Time)
# This avoids timeout during first request
# ============================================
RUN python -c "from transformers import pipeline; \
    pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english'); \
    pipeline('ner', model='dslim/bert-base-NER'); \
    print('✓ Distilled models pre-downloaded')"

# Download small spaCy models
RUN pip install spacy && \
    python -m spacy download en_core_web_sm && \
    python -m spacy download fr_core_news_sm && \
    echo '✓ spaCy models downloaded'

# Pre-download sentence transformer (small version)
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2'); \
    print('✓ Sentence transformer pre-downloaded')"

# Copy application code
COPY syscred/ /app/syscred/

# Create user for HF Spaces (required)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

WORKDIR /app

EXPOSE 7860

# Run with HF Spaces port (7860)
# Increased workers to 4 for better concurrency, timeout 600s
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "4", "--timeout", "600", "syscred.backend_app:app"]
