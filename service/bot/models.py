from django.db import models
from django.contrib.auth.models import User

from common.models import BaseModel


class BotProfileQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.select_related("user")


class BotProfileManager(models.Manager):
    def get_queryset(self):
        return BotProfileQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()


class BotProfile(BaseModel):
    objects = BotProfileManager()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="bot_profile")
    disposition = models.TextField()
    voice = models.TextField()
