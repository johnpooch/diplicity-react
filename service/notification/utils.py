import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_notification_to_users(user_ids, title, body, notification_type, data=None):
    if not user_ids:
        return

    if not getattr(settings, "FIREBASE_APP", None):
        return

    from fcm_django.models import FCMDevice
    from firebase_admin.messaging import Message, Notification

    devices = FCMDevice.objects.filter(user_id__in=user_ids, active=True)
    if not devices.exists():
        return

    message_data = data or {}
    message_data["type"] = notification_type

    message = Message(
        notification=Notification(title=title, body=body),
        data=message_data,
    )

    try:
        devices.send_message(message)
        logger.info(f"Sent {notification_type} notification to {len(user_ids)} users")
    except Exception as e:
        logger.error(f"Failed to send {notification_type} notification: {str(e)}")
