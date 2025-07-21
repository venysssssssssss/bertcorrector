FROM python:3.12-slim

# Maintainer information
LABEL maintainer="bertcorrector-team"
LABEL version="2.0.0"
LABEL description="SpaCy enhancer service for semantic analysis and contextual suggestions"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Create app directory
WORKDIR /app

# Copy Poetry files first for better caching
COPY pyproject.toml poetry.lock* ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root \
    && rm -rf $POETRY_CACHE_DIR

# Download SpaCy Portuguese model
RUN python -m spacy download pt_core_news_lg

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p /app/models

# Set permissions
RUN chmod +x /app/start.sh

# Create non-root user
RUN useradd -m -u 1000 spacy && chown -R spacy:spacy /app
USER spacy

# Expose port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8020/health || exit 1

# Start the application
CMD ["/app/start.sh"]
