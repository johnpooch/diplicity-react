from django.conf import settings


def get_version_data():
    return {
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
    }