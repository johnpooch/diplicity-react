
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

echo "Starting Gunicorn..."
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000
