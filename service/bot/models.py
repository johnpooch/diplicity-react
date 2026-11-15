from django.contrib.auth.models import User
from django.db import models

from bot.constants import BotKind
from common.models import BaseModel


class Bot(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="bot")
    kind = models.CharField(max_length=20, choices=BotKind.KIND_CHOICES)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
