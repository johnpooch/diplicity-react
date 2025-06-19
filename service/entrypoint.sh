#!/bin/sh

set -e

echo "Starting entrypoint script..."

echo "Running database migrations..."
if python manage.py migrate; then
    echo "Migrations completed successfully."
else
    echo "Migration failed!" >&2
    exit 1
fi

echo "Creating superuser if it doesn't exist..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='superuser').exists():
    User.objects.create_superuser('superuser', 'superuser@example.com', '$DJANGO_SUPERUSER_PASSWORD')
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF

echo "Starting Gunicorn..."
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000
