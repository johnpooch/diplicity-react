from django.contrib.auth import get_user_model
from django.db import models

from common.models import BaseModel

User = get_user_model()


class NotificationManager(models.Manager):
    def create_from_event(self, event_type, context):
        # Local import: notification.registry imports this module at top level.
        from notification.registry import get_spec

        spec = get_spec(event_type, context)
        if spec is None:
            return []
        recipient_ids = spec.get_recipients()
        if not recipient_ids:
            return []
        notifications = self.bulk_create(
            [self.model(recipient_id=rid, event_type=event_type) for rid in recipient_ids]
        )
        NotificationDelivery.objects.broadcast(notifications, spec)
        return notifications


class Notification(BaseModel):
    objects = NotificationManager()

    recipient = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="notifications"
    )
    event_type = models.CharField(max_length=100)

    class Meta:
        ordering = ["-created_at"]


class NotificationDeliveryManager(models.Manager):
    def broadcast(self, notifications, spec):
        rendered = [spec.render(channel) for channel in spec.channels]
        email_enabled_ids = None
        deliveries = []
        for notification in notifications:
            for content in rendered:
                if content["channel"] == self.model.Channel.EMAIL:
                    if email_enabled_ids is None:
                        email_enabled_ids = self._email_enabled_ids(
                            [n.recipient_id for n in notifications]
                        )
                    if notification.recipient_id not in email_enabled_ids:
                        continue
                deliveries.append(self.model(notification=notification, **content))
        if not deliveries:
            return []
        self.bulk_create(deliveries)
        # Local import: notification.tasks imports this module at top level.
        from notification.tasks import deliver

        deliver.defer(delivery_ids=[d.id for d in deliveries])
        return deliveries

    def _email_enabled_ids(self, recipient_ids):
        return set(
            User.objects.filter(
                id__in=recipient_ids, profile__email_notifications_enabled=True
            ).values_list("id", flat=True)
        )


class NotificationDelivery(BaseModel):
    class Channel(models.TextChoices):
        PUSH = "push"
        EMAIL = "email"

    class Status(models.TextChoices):
        PENDING = "pending"
        SENT = "sent"
        FAILED = "failed"

    objects = NotificationDeliveryManager()

    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="deliveries")
    channel = models.CharField(max_length=20, choices=Channel.choices)
    heading = models.CharField(max_length=255)
    body = models.TextField()
    link = models.CharField(max_length=500, null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
