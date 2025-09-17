import json

from django.db import models
from .base import BaseModel
from .game import Game
from datetime import timedelta


class Phase(BaseModel):

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
    )

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="phases")
    ordinal = models.PositiveIntegerField(editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
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
        if self.scheduled_resolution and self.status == self.ACTIVE:
            delta = self.scheduled_resolution - timezone.now()
            return max(delta, timedelta(seconds=0))
        return None
