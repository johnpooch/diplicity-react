from django.contrib.auth.models import User
from django.db import models

from common.models import BaseModel
from bot_profile.constants import BOT_USER_USERNAME


class BotProfileQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.select_related("user")

    def available_for_game(self, game):
        return (
            self.select_related("user__profile")
            .exclude(user__username=BOT_USER_USERNAME)
            .exclude(user__members__game=game)
            .order_by("user__profile__name")
        )


class BotProfileManager(models.Manager):
    def get_queryset(self):
        return BotProfileQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def available_for_game(self, game):
        return self.get_queryset().available_for_game(game)


class BotProfile(BaseModel):
    objects = BotProfileManager()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="bot_profile")
    disposition = models.TextField()
    voice = models.TextField()
