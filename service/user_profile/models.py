from django.db import models
from django.contrib.auth.models import User

from common.constants import (
    RELIABILITY_ABANDONED_THRESHOLD,
    RELIABILITY_MIN_GAMES,
    ReliabilityTier,
)
from common.models import BaseModel


class UserProfileQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.select_related("user")


class UserProfileManager(models.Manager):
    def get_queryset(self):
        return UserProfileQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()


class UserProfile(BaseModel):
    objects = UserProfileManager()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    picture = models.URLField(null=True, blank=True)
    games_finished = models.PositiveIntegerField(default=0)
    games_abandoned_recent = models.PositiveSmallIntegerField(default=0)

    @property
    def reliability_tier(self):
        if self.games_finished < RELIABILITY_MIN_GAMES:
            return ReliabilityTier.NEW_PLAYER
        if self.games_abandoned_recent >= RELIABILITY_ABANDONED_THRESHOLD:
            return ReliabilityTier.UNRELIABLE
        return ReliabilityTier.RELIABLE
