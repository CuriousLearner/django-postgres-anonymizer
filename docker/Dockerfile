# Simplified Dockerfile for django-postgres-anon testing and development

# Base Python image
FROM python:3.10-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and setup files
COPY requirements.txt .
COPY pyproject.toml .
COPY README.md .
COPY MANIFEST.in .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Development/Test image
FROM base AS development

# Install test and development dependencies
RUN pip install --no-cache-dir \
    pytest pytest-django pytest-cov coverage \
    flake8 black isort mypy bandit safety \
    ipython django-extensions

# Copy application code
COPY django_postgres_anon/ ./django_postgres_anon/
COPY tests/ ./tests/
COPY example_project/ ./example_project/

# Install package in development mode
RUN pip install -e .

# Create directories for reports
RUN mkdir -p /app/reports

# Default command
CMD ["pytest", "tests/", "-v"]

# Production image (minimal)
FROM base AS production

# Copy only necessary files
COPY django_postgres_anon/ ./django_postgres_anon/

# Install package
RUN pip install .

# Non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app

CMD ["python", "-c", "import django_postgres_anon; print(f'Django PostgreSQL Anonymizer v{django_postgres_anon.__version__}')"]
