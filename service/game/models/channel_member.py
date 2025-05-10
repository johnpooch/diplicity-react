from django.db import models
from .base import BaseModel
from .member import Member
from .channel import Channel


class ChannelMember(BaseModel):
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="member_channels"
    )
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="member_channels"
    )
