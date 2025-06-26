from django.conf import settings

from .. import models
from .base_service import BaseService


class VersionService(BaseService):
    def get(self):
        return {
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
        }
