# This Dockerfile is specifically for the codegen service.
# It includes both frontend (Node.js) and backend (Python) dependencies.
#
# The backend requires Django 6, which needs Python >=3.12, so the image is
# based on python:3.12 and the Node.js runtime is copied in from the official
# Node image. Both images are Debian bookworm based, so the copied Node binary
# is ABI-compatible.

# Node.js runtime source
FROM node:24.17.0-bookworm-slim AS node

# Python 3.12 base
FROM python:3.14-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies (build-essential also provides libstdc++6, which
# the copied Node binary depends on)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Bring in the Node.js runtime and npm/npx from the official Node image
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

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
