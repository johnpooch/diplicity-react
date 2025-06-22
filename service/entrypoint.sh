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
