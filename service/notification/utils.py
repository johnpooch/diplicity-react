import logging

from django.conf import settings

from common.constants import NotificationDeliveryStatus

logger = logging.getLogger(__name__)


def _delivery_status(firebase_configured, has_device, send_succeeded):
    if not firebase_configured:
        return NotificationDeliveryStatus.SKIPPED
    if not has_device:
        return NotificationDeliveryStatus.NO_DEVICE
    if send_succeeded:
        return NotificationDeliveryStatus.SENT
    return NotificationDeliveryStatus.FAILED


def _record_notifications(
    user_ids, title, body, notification_type, data, firebase_configured, users_with_devices, send_succeeded, send_error
):
    try:
        from notification.models import Notification

        records = []
        for user_id in user_ids:
            status = _delivery_status(
                firebase_configured, user_id in users_with_devices, send_succeeded
            )
            records.append(
                Notification(
                    user_id=user_id,
                    game_id=data.get("game_id"),
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    data=data,
                    delivery_status=status,
                    error=send_error if status == NotificationDeliveryStatus.FAILED else None,
                )
            )
        Notification.objects.bulk_create(records)
    except Exception as e:
        logger.error(f"Failed to record {notification_type} notifications: {str(e)}")


def send_notification_to_users(user_ids, title, body, notification_type, data=None):
    if not user_ids:
        return

    message_data = dict(data or {})
    message_data["type"] = notification_type

    firebase_configured = bool(getattr(settings, "FIREBASE_APP", None))

    users_with_devices = set()
    devices = None
    if firebase_configured:
        from fcm_django.models import FCMDevice

        devices = FCMDevice.objects.filter(user_id__in=user_ids, active=True)
        users_with_devices = set(devices.values_list("user_id", flat=True))

    send_succeeded = False
    send_error = None
    if users_with_devices:
        from firebase_admin.messaging import Message, Notification

        message = Message(
            notification=Notification(title=title, body=body),
            data=message_data,
        )
        try:
            devices.send_message(message)
            send_succeeded = True
            logger.info(f"Sent {notification_type} notification to {len(user_ids)} users")
        except Exception as e:
            send_error = str(e)
            logger.error(f"Failed to send {notification_type} notification: {send_error}")

    _record_notifications(
        user_ids=user_ids,
        title=title,
        body=body,
        notification_type=notification_type,
        data=message_data,
        firebase_configured=firebase_configured,
        users_with_devices=users_with_devices,
        send_succeeded=send_succeeded,
        send_error=send_error,
    )
