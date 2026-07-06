import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from procrastinate.contrib.django import app

from notification import utils as notification_utils

logger = logging.getLogger(__name__)


@app.task(name="notification.send_notification")
def send_notification(user_ids, title, body, notification_type, data=None):
    logger.info(f"Running send_notification task ({notification_type})")
    notification_utils.send_notification_to_users(
        user_ids=user_ids,
        title=title,
        body=body,
        notification_type=notification_type,
        data=data,
    )


@app.periodic(cron="17 3 * * *")
@app.task(name="notification.prune_old_notifications")
def prune_old_notifications(timestamp):
    from notification.models import Notification

    retention_days = getattr(settings, "NOTIFICATION_RETENTION_DAYS", 90)
    cutoff = timezone.now() - timedelta(days=retention_days)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info(f"Pruned {deleted} notifications older than {retention_days} days")
    return deleted
