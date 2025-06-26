from .. import models
from .base_service import BaseService


class VariantService(BaseService):
    def __init__(self, user):
        self.user = user

    def list(self):
        return models.Variant.objects.all()
