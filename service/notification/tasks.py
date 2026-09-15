import logging
from datetime import timedelta

from django.utils import timezone
from procrastinate.contrib.django import app

from notification import utils as notification_utils
from notification.models import Notification, NotificationDelivery

logger = logging.getLogger(__name__)

PRUNE_AFTER_DAYS = 30
DELIVER_MAX_AGE_HOURS = 1
NO_RECIPIENT_ERROR = "recipient no longer exists"


@app.task(name="notification.deliver", retry=3)
def deliver(delivery_ids):
    deliveries = list(
        NotificationDelivery.objects.filter(
            id__in=delivery_ids, status=NotificationDelivery.Status.PENDING
        ).select_related("notification")
    )
    if not deliveries:
        return
    fresh = NotificationDelivery.objects.expire_stale(deliveries, timedelta(hours=DELIVER_MAX_AGE_HOURS))
    if not fresh:
        return
    try:
        errors = _send_push(fresh)
    except Exception as e:
        errors = {d.notification.recipient_id: str(e) for d in fresh}
    for delivery in fresh:
        error = errors.get(delivery.notification.recipient_id, NO_RECIPIENT_ERROR)
        delivery.status = NotificationDelivery.Status.FAILED if error else NotificationDelivery.Status.SENT
        delivery.error = error
    NotificationDelivery.objects.bulk_update(fresh, ["status", "error"])


def _send_push(deliveries):
    first = deliveries[0]
    recipient_ids = [d.notification.recipient_id for d in deliveries if d.notification.recipient_id is not None]
    return notification_utils.send_notification_to_users(
        user_ids=recipient_ids,
        title=first.heading,
        body=first.body,
        notification_type=first.notification.event_type,
        data=first.data,
    )


@app.periodic(cron="0 3 * * *")
@app.task(name="notification.prune")
def prune(timestamp):
    cutoff = timezone.now() - timedelta(days=PRUNE_AFTER_DAYS)
    Notification.objects.filter(created_at__lt=cutoff).delete()
