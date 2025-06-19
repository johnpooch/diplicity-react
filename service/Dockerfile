# Base stage: Install dependencies and set up the app
FROM python:3.9-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt dev_requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt -r dev_requirements.txt

# Copy the application code
COPY . /app/

# Expose the port the app runs on
EXPOSE 8000

# Development stage: Default user
FROM base AS development

# Use the default root user for development
USER root

# Worker stage: Non-root user
FROM base AS worker

# Create a non-root user for the worker
RUN useradd -ms /bin/bash celeryuser

# Switch to the non-root user
USER celeryuser 

CMD ["celery", "-A", "project", "worker", "--loglevel=info"]

# Production stage: Use gunicorn
FROM base AS production

# Install gunicorn
RUN pip install gunicorn

# Create a non-root user
RUN useradd -ms /bin/bash appuser

# Create staticfiles directory and set permissions
RUN mkdir -p /app/staticfiles && chown -R appuser:appuser /app

# Copy and set up entrypoint script
COPY --chmod=755 entrypoint.sh /entrypoint.sh

# Switch to non-root user
USER appuser

ENTRYPOINT ["/entrypoint.sh"]
