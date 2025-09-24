from django.db import models

from game.models.base import BaseModel
from common.constants import PhaseStatus


class Variant(BaseModel):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=200, blank=True)

    @property
    def template_phase(self):
        return self.phases.get(game=None, status=PhaseStatus.TEMPLATE)
