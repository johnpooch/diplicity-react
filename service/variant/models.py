import hashlib

from django.db import models
from django.db.models import Prefetch

from common.models import BaseModel
from common.constants import PhaseStatus
from phase.models import Phase


def default_victory_conditions():
    return {"soloVictorySupplyCenters": 18, "gameEndsYear": None, "drawAfterYear": None}


def default_phase_progression():
    return {
        "seasons": ["Spring", "Fall"],
        "transitions": [
            {"from": {"season": "Spring", "type": "Movement"},
             "to": {"season": "Spring", "type": "Retreat", "yearDelta": 0}},
            {"from": {"season": "Spring", "type": "Retreat"},
             "to": {"season": "Fall", "type": "Movement", "yearDelta": 0}},
            {"from": {"season": "Fall", "type": "Movement"},
             "to": {"season": "Fall", "type": "Retreat", "yearDelta": 0}},
            {"from": {"season": "Fall", "type": "Retreat"},
             "to": {"season": "Fall", "type": "Adjustment", "yearDelta": 0}},
            {"from": {"season": "Fall", "type": "Adjustment"},
             "to": {"season": "Spring", "type": "Movement", "yearDelta": 1}},
        ],
    }


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

    def with_game_creation_data(self):
        template_phase_prefetch = Prefetch(
            "phases",
            queryset=Phase.objects.filter(
                game=None,
                status=PhaseStatus.TEMPLATE
            ).prefetch_related(
                "units__nation",
                "units__province",
                "supply_centers__nation",
                "supply_centers__province",
            ),
            to_attr="template_phases",
        )

        return self.prefetch_related(
            "nations",
            template_phase_prefetch,
        )


class VariantManager(models.Manager):
    def get_queryset(self):
        return VariantQuerySet(self.model, using=self._db)

    def with_game_creation_data(self):
        return self.get_queryset().with_game_creation_data()


class Variant(BaseModel):
    objects = VariantManager()

    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=200, blank=True)
    victory_conditions = models.JSONField(default=default_victory_conditions)
    adjudication_modifiers = models.JSONField(default=list)
    phase_progression = models.JSONField(default=default_phase_progression)
    rules = models.TextField(blank=True, default="")

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


class VariantSvg(BaseModel):
    variant = models.OneToOneField(Variant, on_delete=models.CASCADE, related_name="svg")
    svg = models.TextField()
    content_hash = models.CharField(max_length=64, editable=False)

    def save(self, *args, **kwargs):
        self.content_hash = hashlib.sha256(self.svg.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.variant_id} SVG"
