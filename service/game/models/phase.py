import json

from django.db import models
from .base import BaseModel
from .game import Game
from datetime import timedelta
from common.constants import PhaseStatus


class Phase(BaseModel):

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="phases", null=True, blank=True)
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, related_name="phases", null=True, blank=True)
    ordinal = models.PositiveIntegerField(editable=False)
    status = models.CharField(max_length=20, choices=PhaseStatus.STATUS_CHOICES, default=PhaseStatus.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    season = models.CharField(max_length=10)
    year = models.IntegerField()
    type = models.CharField(max_length=10)
    scheduled_resolution = models.DateTimeField(null=True, blank=True)
    options = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Check if the instance is being created
            last_ordinal = (
                Phase.objects.filter(game=self.game).aggregate(models.Max("ordinal"))[
                    "ordinal__max"
                ]
                or 0
            )
            self.ordinal = last_ordinal + 1
        super().save(*args, **kwargs)

    @property
    def name(self):
        return f"{self.season} {self.year}, {self.type}"

    @property
    def options_dict(self):
        if self.options:
            try:
                return json.loads(str(self.options))
            except json.JSONDecodeError:
                return {}
        return {}

    @property
    def remaining_time(self):
        from django.utils import timezone
        if self.scheduled_resolution and self.status == PhaseStatus.ACTIVE:
            delta = self.scheduled_resolution - timezone.now()
            return max(delta, timedelta(seconds=0))
        return None
