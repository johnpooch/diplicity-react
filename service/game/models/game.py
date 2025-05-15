from django.db import models
from .base import BaseModel
from datetime import timedelta


class Game(BaseModel):

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

    variant = models.ForeignKey(
        "Variant", on_delete=models.CASCADE, related_name="games"
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
    resolution_task = models.OneToOneField(
        "Task", on_delete=models.SET_NULL, null=True, blank=True, related_name="game"
    )

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
