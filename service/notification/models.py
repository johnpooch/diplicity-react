from django.conf import settings
from django.db import models

from common.constants import NotificationDeliveryStatus
from common.models import BaseModel


class Notification(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    game_id = models.CharField(max_length=150, null=True, blank=True, db_index=True)
    notification_type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    delivery_status = models.CharField(
        max_length=20,
        choices=NotificationDeliveryStatus.DELIVERY_STATUS_CHOICES,
        default=NotificationDeliveryStatus.SENT,
    )
    error = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"{self.notification_type} -> {self.user_id} ({self.delivery_status})"
