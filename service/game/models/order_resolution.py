from django.db import models
from .base import BaseModel
from .order import Order


class OrderResolution(BaseModel):

    SUCCEEDED = "succeeded"
    BOUNCED = "bounced"

    STATUS_CHOICES = [
        (SUCCEEDED, "Succeeded"),
        (BOUNCED, "Bounced"),
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="resolution"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
