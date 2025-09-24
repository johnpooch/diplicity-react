from datetime import timedelta
import re
import uuid

from django.db import models
from .base import BaseModel


class GameQuerySet(models.QuerySet):
    def with_variant(self):
        return self.select_related("variant")

    def with_phases(self):
        return self.prefetch_related(
            "phases__units",
            "phases__supply_centers",
            "phases__phase_states",
        )

    def with_members(self):
        return self.prefetch_related("members__user__profile")

    def includes_user(self, user):
        return self.filter(members__user=user)

    def joinable(self, user):
        return self.filter(status=Game.PENDING).exclude(members__user=user)


class GameManager(models.Manager):
    def get_queryset(self):
        return GameQuerySet(self.model, using=self._db)


class Game(BaseModel):
    objects = GameManager()

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
    )

    TWENTY_FOUR_HOURS = "24 hours"

    MOVEMENT_PHASE_DURATION_CHOICES = ((TWENTY_FOUR_HOURS, "24 hours"),)

    RANDOM = "random"
    ORDERED = "ordered"

    NATION_ASSIGNMENT_CHOICES = (
        (RANDOM, "Random"),
        (ORDERED, "Ordered"),
    )

    id = models.CharField(max_length=150, primary_key=True)
    variant = models.ForeignKey(
        "variant.Variant", on_delete=models.CASCADE, related_name="games"
    )
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    private = models.BooleanField(default=False)
    movement_phase_duration = models.CharField(
        max_length=20,
        choices=MOVEMENT_PHASE_DURATION_CHOICES,
        default=TWENTY_FOUR_HOURS,
    )
    nation_assignment = models.CharField(
        max_length=20,
        choices=NATION_ASSIGNMENT_CHOICES,
        default=RANDOM,
    )

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self._generate_id()
        super().save(*args, **kwargs)

    def _generate_id(self):
        # Convert name to lowercase and replace spaces with hyphens
        base_id = re.sub(r"[^a-z0-9]+", "-", self.name.lower())
        base_id = re.sub(r"^-+|-+$", "", base_id)  # Remove leading/trailing hyphens

        # Check if this base_id already exists
        if not Game.objects.filter(id=base_id).exists():
            return base_id

        # If it exists, append a short UUID
        return f"{base_id}-{str(uuid.uuid4())[:8]}"

    @property
    def current_phase(self):
        return self.phases.last()

    def can_join(self, user):
        user_is_member = self.members.filter(user__id=user.id).exists()
        game_is_pending = self.status == self.PENDING
        return not user_is_member and game_is_pending

    def can_leave(self, user):
        user_is_member = self.members.filter(user__id=user.id).exists()
        game_is_pending = self.status == self.PENDING
        return user_is_member and game_is_pending

    def get_phase_duration_seconds(self):
        if self.movement_phase_duration == self.TWENTY_FOUR_HOURS:
            return 24 * 60 * 60
        return 0

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["variant"]),
        ]
