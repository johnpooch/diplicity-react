from django.db import models

from common.models import BaseModel
from common.constants import PhaseStatus


class Variant(BaseModel):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=200, blank=True)

    @property
    def template_phase(self):
        # Use prefetched template_phases if available (from Prefetch object)
        if hasattr(self, 'template_phases'):
            return self.template_phases[0] if self.template_phases else None

        # Fall back to database query if not prefetched
        for phase in self.phases.all():
            if phase.game is None and phase.status == PhaseStatus.TEMPLATE:
                return phase
        return None
