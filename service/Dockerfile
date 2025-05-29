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

# Set the startup command
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

# Worker stage: Non-root user
FROM base AS worker

# Create a non-root user for the worker
RUN useradd -ms /bin/bash celeryuser

# Switch to the non-root user
USER celeryuser 