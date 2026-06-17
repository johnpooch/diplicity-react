import hashlib

from django.conf import settings
from django.db import models
from django.db.models import Prefetch

from common.models import BaseModel
from common.constants import PhaseStatus, VariantStatus
from phase.models import Phase


def default_victory_conditions():
    return [{"type": "supply-center-majority", "supplyCenters": 18}]


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
        from nation.models import Nation
        template_phase_prefetch = Prefetch(
            "phases",
            queryset=Phase.objects.filter(game=None, status=PhaseStatus.TEMPLATE).prefetch_related(
                "units__nation__flag",
                "units__province__parent",
                "units__province__named_coasts",
                "units__dislodged_by",
                "supply_centers__nation__flag",
                "supply_centers__province__parent",
                "supply_centers__province__named_coasts",
                "phase_states",
            ),
            to_attr="template_phases",
        )
        nations_prefetch = Prefetch("nations", queryset=Nation.objects.select_related("flag"))

        return self.select_related("svg", "owner").defer("svg__svg").prefetch_related(
            # Variant data with optimized template phase
            "provinces__parent",
            "provinces__named_coasts",
            nations_prefetch,
            template_phase_prefetch,
        )

    def with_game_creation_data(self):
        from nation.models import Nation
        template_phase_prefetch = Prefetch(
            "phases",
            queryset=Phase.objects.filter(
                game=None,
                status=PhaseStatus.TEMPLATE
            ).prefetch_related(
                "units__nation__flag",
                "units__province",
                "supply_centers__nation__flag",
                "supply_centers__province",
            ),
            to_attr="template_phases",
        )
        nations_prefetch = Prefetch("nations", queryset=Nation.objects.select_related("flag"))

        return self.prefetch_related(
            nations_prefetch,
            template_phase_prefetch,
        )


class VariantManager(models.Manager):
    def get_queryset(self):
        return VariantQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def with_game_creation_data(self):
        return self.get_queryset().with_game_creation_data()


class Variant(BaseModel):
    objects = VariantManager()

    id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=200, blank=True)
    victory_conditions = models.JSONField(default=default_victory_conditions)
    adjudication_modifiers = models.JSONField(default=list, blank=True)
    phase_progression = models.JSONField(default=default_phase_progression)
    rules = models.TextField(blank=True, default="")
    dominance_rules = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20,
        choices=VariantStatus.STATUS_CHOICES,
        default=VariantStatus.DRAFT,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_variants",
    )

    @property
    def slug(self):
        if self.owner_id is not None:
            prefix = f"{self.owner_id}-"
            if self.id.startswith(prefix):
                return self.id[len(prefix):]
        return self.id

    @property
    def solo_victory_supply_centers(self):
        for condition in self.victory_conditions:
            if condition["type"] == "supply-center-majority":
                return condition["supplyCenters"]
        return None

    @property
    def victory_conditions_summary(self):
        summary = {
            "soloVictorySupplyCenters": None,
            "gameEndsYear": None,
            "drawAfterYear": None,
        }
        for condition in self.victory_conditions:
            if condition["type"] == "supply-center-majority":
                summary["soloVictorySupplyCenters"] = condition["supplyCenters"]
            elif condition["type"] == "timed-resolution":
                if condition["resolution"] == "shared-draw":
                    summary["drawAfterYear"] = condition["year"]
                else:
                    summary["gameEndsYear"] = condition["year"]
        return summary

    @property
    def template_phase(self):
        # Use prefetched template_phases if available (from Prefetch object)
        if hasattr(self, "template_phases"):
            return self.template_phases[0] if self.template_phases else None

        return self.phases.filter(game__isnull=True, status=PhaseStatus.TEMPLATE).first()


class VariantSvg(BaseModel):
    variant = models.OneToOneField(Variant, on_delete=models.CASCADE, related_name="svg")
    svg = models.TextField()
    content_hash = models.CharField(max_length=64, editable=False)

    def save(self, *args, **kwargs):
        from variant.utils import normalize_dsvg, sanitize_svg

        self.svg = sanitize_svg(normalize_dsvg(self.svg))
        self.content_hash = hashlib.sha256(self.svg.encode()).hexdigest()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"svg", "content_hash"}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.variant_id} SVG"
