import logging
from datetime import timedelta

from django.utils import timezone
from procrastinate.contrib.django import app

from email_service import utils as email_utils
from notification import utils as notification_utils
from notification.models import Notification, NotificationDelivery

logger = logging.getLogger(__name__)

PRUNE_AFTER_DAYS = 30


@app.task(name="notification.deliver", retry=3)
def deliver(delivery_ids):
    deliveries = list(
        NotificationDelivery.objects.filter(id__in=delivery_ids).select_related("notification")
    )
    if not deliveries:
        return
    _deliver_channel(deliveries, NotificationDelivery.Channel.PUSH, _send_push)
    _deliver_channel(deliveries, NotificationDelivery.Channel.EMAIL, _send_email)


def _deliver_channel(deliveries, channel, send):
    group = [d for d in deliveries if d.channel == channel]
    if not group:
        return
    ids = [d.id for d in group]
    try:
        send(group)
        NotificationDelivery.objects.filter(id__in=ids).update(status=NotificationDelivery.Status.SENT)
    except Exception as e:
        NotificationDelivery.objects.filter(id__in=ids).update(
            status=NotificationDelivery.Status.FAILED, error=str(e)
        )


def _send_push(deliveries):
    first = deliveries[0]
    recipient_ids = [d.notification.recipient_id for d in deliveries if d.notification.recipient_id is not None]
    notification_utils.send_notification_to_users(
        user_ids=recipient_ids,
        title=first.heading,
        body=first.body,
        notification_type=first.notification.event_type,
        data=first.data,
    )


def _send_email(deliveries):
    first = deliveries[0]
    recipient_ids = [d.notification.recipient_id for d in deliveries if d.notification.recipient_id is not None]
    email_utils.send_email_to_users(user_ids=recipient_ids, subject=first.heading, html=first.body)


@app.periodic(cron="0 3 * * *")
@app.task(name="notification.prune")
def prune(timestamp):
    cutoff = timezone.now() - timedelta(days=PRUNE_AFTER_DAYS)
    Notification.objects.filter(created_at__lt=cutoff).delete()
