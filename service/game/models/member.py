from django.db import models
from django.contrib.auth import get_user_model
from .base import BaseModel
from .game import Game

User = get_user_model()


class Member(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="members")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="members")
    nation = models.CharField(max_length=100, blank=True, null=True)
    won = models.BooleanField(default=False)
    drew = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    kicked = models.BooleanField(default=False)
