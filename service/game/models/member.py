from django.db import models
from django.contrib.auth import get_user_model
from .base import BaseModel
from .game import Game

User = get_user_model()


class Member(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="members")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="members")
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="members")
    won = models.BooleanField(default=False)
    drew = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    kicked = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["game", "user"]),
            models.Index(fields=["user"]),
            models.Index(fields=["game"]),
        ]
