#!/bin/sh

set -e

PROCESS_ROLE="${PROCESS_ROLE:-web}"

echo "Starting entrypoint script (role: $PROCESS_ROLE)..."

if [ "$PROCESS_ROLE" = "worker" ]; then
    echo "Waiting for migrations to complete before starting Procrastinate worker..."
    attempt=0
    until python manage.py migrate --check; do
        attempt=$((attempt + 1))
        if [ "$attempt" -ge 60 ]; then
            echo "Timed out waiting for migrations to complete." >&2
            exit 1
        fi
        sleep 5
    done
    echo "Starting Procrastinate worker..."
    exec python manage.py procrastinate worker
fi

echo "Running database migrations and ensuring superuser exists..."
if python manage.py shell << 'EOF'
import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection

MIGRATION_LOCK_ID = 727272001

with connection.cursor() as cursor:
    cursor.execute("SELECT pg_advisory_lock(%s)", [MIGRATION_LOCK_ID])
try:
    call_command("migrate")
finally:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_unlock(%s)", [MIGRATION_LOCK_ID])

User = get_user_model()
if not User.objects.filter(username="superuser").exists():
    User.objects.create_superuser("superuser", "superuser@example.com", os.environ.get("DJANGO_SUPERUSER_PASSWORD"))
    print("Superuser created")
EOF
then
    echo "Migrations completed successfully."
else
    echo "Migration or superuser creation failed!" >&2
    exit 1
fi

if [ "$SEED_STAGING_DATA" = "True" ]; then
    echo "Seeding staging test data..."
    if ! python manage.py seed_staging --skip-if-seeded; then
        echo "Seeding staging test data failed!" >&2
        exit 1
    fi
fi

if [ -n "$RAILWAY_GIT_COMMIT_SHA" ] && [ -n "$HONEYCOMB_MARKERS_API_KEY" ] && [ "$RAILWAY_ENVIRONMENT_NAME" = "production" ]; then
    MARKER_URL="https://api.honeycomb.io/1/markers/__all__"
    curl --silent --show-error --fail --max-time 10 \
        --request POST "$MARKER_URL" \
        --header "X-Honeycomb-Team: $HONEYCOMB_MARKERS_API_KEY" \
        --header "Content-Type: application/json" \
        --data "{\"type\": \"backend-deploy\", \"message\": \"Backend deploy $RAILWAY_GIT_COMMIT_SHA\"}" \
        || echo "Failed to create Honeycomb marker." >&2
fi

echo "Starting Gunicorn..."
exec gunicorn project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --max-requests 2000 \
    --max-requests-jitter 200
