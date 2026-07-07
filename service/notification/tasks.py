import logging

from django.conf import settings
from django.utils import timezone
from procrastinate.contrib.django import app

from common.constants import NotificationDeliveryStatus
from notification.models import Notification

logger = logging.getLogger(__name__)


def _fcm_send(user_ids, title, body, data):
    from fcm_django.models import FCMDevice
    from firebase_admin.messaging import Message, Notification as FCMNotification

    devices = list(FCMDevice.objects.filter(user_id__in=user_ids, active=True))
    if not devices:
        return None

    token_to_user = {device.registration_id: device.user_id for device in devices}
    message = Message(
        notification=FCMNotification(title=title, body=body),
        data=data,
    )
    response = FCMDevice.objects.filter(user_id__in=user_ids, active=True).send_message(message)
    return response, token_to_user


def _attribute_statuses(user_ids, token_to_user, registration_ids_sent, responses):
    tallies = {user_id: {"success": 0, "failure": 0, "error": None} for user_id in token_to_user.values()}
    for token, response in zip(registration_ids_sent or [], responses or []):
        user_id = token_to_user.get(token)
        if user_id is None:
            continue
        if response.success:
            tallies[user_id]["success"] += 1
        else:
            tallies[user_id]["failure"] += 1
            tallies[user_id]["error"] = str(getattr(response, "exception", "") or "")

    statuses = {}
    for user_id in user_ids:
        tally = tallies.get(user_id)
        if not tally or (tally["success"] == 0 and tally["failure"] == 0):
            statuses[user_id] = (NotificationDeliveryStatus.NO_DEVICE, None)
        elif tally["success"] > 0:
            statuses[user_id] = (NotificationDeliveryStatus.SENT, None)
        else:
            statuses[user_id] = (NotificationDeliveryStatus.FAILED, tally["error"])
    return statuses


def _finish(notifications, statuses=None, status=None, error=None):
    now = timezone.now()
    for notification in notifications:
        if statuses is not None:
            notification.delivery_status, notification.error = statuses[notification.user_id]
        else:
            notification.delivery_status, notification.error = status, error
        notification.updated_at = now
    Notification.objects.bulk_update(notifications, ["delivery_status", "error", "updated_at"])


def deliver(notification_ids):
    notifications = list(Notification.objects.filter(id__in=notification_ids))
    if not notifications:
        return

    notification_type = notifications[0].notification_type
    logger.info(f"Delivering {notification_type} notifications")

    if not getattr(settings, "FIREBASE_APP", None):
        _finish(notifications, status=NotificationDeliveryStatus.SKIPPED)
        return

    user_ids = [notification.user_id for notification in notifications]
    data = {**(notifications[0].data or {}), "type": notification_type}

    try:
        result = _fcm_send(user_ids, notifications[0].title, notifications[0].body, data)
    except Exception as e:
        error = str(e)
        logger.error(f"Failed to send {notification_type} notification: {error}")
        _finish(notifications, status=NotificationDeliveryStatus.FAILED, error=error)
        return

    if result is None:
        _finish(notifications, status=NotificationDeliveryStatus.NO_DEVICE)
        return

    response, token_to_user = result
    statuses = _attribute_statuses(
        user_ids, token_to_user, response.registration_ids_sent, response.response.responses
    )
    logger.info(f"Sent {notification_type} notification to {len(user_ids)} users")
    _finish(notifications, statuses=statuses)


@app.task(name="notification.deliver")
def deliver_notifications(notification_ids):
    deliver(notification_ids)


@app.periodic(cron="17 3 * * *")
@app.task(name="notification.prune_old_notifications")
def prune_old_notifications(timestamp):
    deleted, _ = Notification.objects.prune_old()
    logger.info(f"Pruned {deleted} old notifications")
    return deleted
