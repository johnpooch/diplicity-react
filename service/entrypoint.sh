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

echo "Running database migrations..."
if python manage.py migrate; then
    echo "Migrations completed successfully."
else
    echo "Migration failed!" >&2
    exit 1
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser (deleting existing if present)..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.filter(username='superuser').exists():
    User.objects.filter(username='superuser').delete()
    print("Existing superuser deleted")
User.objects.create_superuser('superuser', 'superuser@example.com', '$DJANGO_SUPERUSER_PASSWORD')
print("Superuser created successfully")
EOF

echo "Starting Gunicorn..."
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000
