from django.db import models
from django.db.models import Prefetch

from common.models import BaseModel
from common.constants import PhaseStatus
from phase.models import Phase


class VariantQuerySet(models.QuerySet):

    def with_related_data(self):
        template_phase_prefetch = Prefetch(
            "phases",
            queryset=Phase.objects.filter(game=None, status=PhaseStatus.TEMPLATE).prefetch_related(
                "units__nation",
                "units__province__parent",
                "units__province__named_coasts",
                "units__dislodged_by",
                "supply_centers__nation",
                "supply_centers__province__parent",
                "supply_centers__province__named_coasts",
                "phase_states",
            ),
            to_attr="template_phases",
        )

        return self.prefetch_related(
            # Variant data with optimized template phase
            "provinces__parent",
            "provinces__named_coasts",
            "nations",
            template_phase_prefetch,
        )


class VariantManager(models.Manager):
    def get_queryset(self):
        return VariantQuerySet(self.model, using=self._db)


class Variant(BaseModel):
    objects = VariantManager()

    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=200, blank=True)

    @property
    def template_phase(self):
        # Use prefetched template_phases if available (from Prefetch object)
        if hasattr(self, "template_phases"):
            return self.template_phases[0] if self.template_phases else None

        # Fall back to database query if not prefetched
        for phase in self.phases.all():
            if phase.game is None and phase.status == PhaseStatus.TEMPLATE:
                return phase
        return None
