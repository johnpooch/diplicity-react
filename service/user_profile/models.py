from django.db import models
from django.contrib.auth.models import User

from common.constants import Commitment, UserKind
from common.models import BaseModel


class UserProfileQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.select_related("user")

    def addable_to_game(self, game):
        return (
            self.filter(kind__in=UserKind.BOT_KINDS)
            .select_related("user")
            .exclude(user__members__game=game)
            .order_by("name")
        )


class UserProfileManager(models.Manager):
    def get_queryset(self):
        return UserProfileQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def addable_to_game(self, game):
        return self.get_queryset().addable_to_game(game)


class UserProfile(BaseModel):
    objects = UserProfileManager()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    picture = models.URLField(null=True, blank=True)
    email_notifications_enabled = models.BooleanField(default=False)
    commitment = models.CharField(
        max_length=20,
        choices=Commitment.COMMITMENT_CHOICES,
        default=Commitment.UNDEFINED,
    )
    kind = models.CharField(
        max_length=20,
        choices=UserKind.KIND_CHOICES,
        default=UserKind.HUMAN,
    )

    @property
    def is_bot(self):
        return self.kind != UserKind.HUMAN
