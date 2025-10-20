"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from project.otel_config import configure_opentelemetry

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

configure_opentelemetry()

application = get_wsgi_application()
