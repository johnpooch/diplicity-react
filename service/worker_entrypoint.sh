#!/bin/sh

set -e

# Start the health check server in the background
echo "Starting health check server..."
gunicorn --bind 0.0.0.0:8000 --workers 1 worker.health_check:app &

# Start the Celery worker in the foreground
echo "Starting Celery worker..."
celery -A project worker --loglevel=info 