# This Dockerfile is specifically for development purposes.
# It includes both frontend (Node.js) and backend (Python) dependencies
# to support development of the full stack application in a single container.

# Base image with Node.js and Python
FROM node:current-bullseye-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev \
    git \
    bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install global npm packages
RUN npm install -g npm@latest

# Install Claude CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Set working directory
WORKDIR /app

# Copy Python configuration files
COPY ./service/requirements.txt ./service/dev_requirements.txt ./service/pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r dev_requirements.txt

# Install Node.js dependencies
COPY ./packages/web/package.json ./packages/web/package-lock.json /app/packages/web/
WORKDIR /app/packages/web
RUN npm install

WORKDIR /app

# Expose ports for React (5173) and Django (8000)
EXPOSE 5173 8000

# Default command
CMD ["bash"] 