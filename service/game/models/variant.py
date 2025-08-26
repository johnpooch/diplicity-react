from django.db import models

from .base import BaseModel


class Variant(BaseModel):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=200, blank=True)
    nations_data = models.JSONField()
    start_data = models.JSONField()
    provinces_data = models.JSONField()

    @property
    def nations(self):
        return self.nations_data

    @property
    def start(self):
        return self.start_data

    @property
    def provinces(self):
        return self.provinces_data
