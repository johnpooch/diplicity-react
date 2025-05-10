from django.db import models
from .base import BaseModel


class Channel(BaseModel):
    name = models.CharField(max_length=250)
    private = models.BooleanField(default=False)
    game = models.ForeignKey(
        "game.Game", on_delete=models.CASCADE, related_name="channels"
    )
    members = models.ManyToManyField(
        "game.Member",
        through="game.ChannelMember",
        related_name="channels",
    )
