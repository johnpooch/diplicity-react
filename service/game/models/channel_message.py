from django.db import models
from django.contrib.auth import get_user_model
from .base import BaseModel
from .channel import Channel


class ChannelMessage(BaseModel):
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        "game.Member", on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField()
