from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.constants import NotificationDeliveryStatus
from common.models import BaseModel


class NotificationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def pending(self):
        return self.filter(delivery_status=NotificationDeliveryStatus.PENDING)

    def of_type(self, notification_type):
        return self.filter(notification_type=notification_type)


class NotificationManager(models.Manager):
    def get_queryset(self):
        return NotificationQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def pending(self):
        return self.get_queryset().pending()

    def of_type(self, notification_type):
        return self.get_queryset().of_type(notification_type)

    def broadcast(self, user_ids, title, body, notification_type, data=None):
        user_ids = [user_id for user_id in dict.fromkeys(user_ids) if user_id is not None]
        if not user_ids:
            return []

        game_id = (data or {}).get("game_id")
        notifications = self.bulk_create(
            [
                self.model(
                    user_id=user_id,
                    game_id=game_id,
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    data=data or {},
                    delivery_status=NotificationDeliveryStatus.PENDING,
                )
                for user_id in user_ids
            ]
        )

        from notification.tasks import deliver_notifications

        deliver_notifications.defer(notification_ids=[n.id for n in notifications])
        return notifications

    def prune_old(self, days=None):
        if days is None:
            days = getattr(settings, "NOTIFICATION_RETENTION_DAYS", 90)
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(created_at__lt=cutoff).delete()


class Notification(BaseModel):
    objects = NotificationManager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    game_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    notification_type = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    delivery_status = models.CharField(
        max_length=16,
        choices=NotificationDeliveryStatus.DELIVERY_STATUS_CHOICES,
        default=NotificationDeliveryStatus.PENDING,
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
