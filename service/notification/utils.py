import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

PUSH_TTL = timedelta(hours=1)


def build_push_message(title, body, notification_type, data=None):
    from firebase_admin.messaging import (
        APNSConfig,
        AndroidConfig,
        Message,
        Notification,
        WebpushConfig,
    )

    message_data = dict(data or {})
    message_data["type"] = notification_type
    expiration = int((timezone.now() + PUSH_TTL).timestamp())

    return Message(
        notification=Notification(title=title, body=body),
        data=message_data,
        android=AndroidConfig(ttl=PUSH_TTL),
        apns=APNSConfig(headers={"apns-expiration": str(expiration)}),
        webpush=WebpushConfig(headers={"TTL": str(int(PUSH_TTL.total_seconds()))}),
    )


def send_notification_to_users(user_ids, title, body, notification_type, data=None):
    if not user_ids:
        return

    if not getattr(settings, "FIREBASE_APP", None):
        return

    from fcm_django.models import FCMDevice

    devices = FCMDevice.objects.filter(user_id__in=user_ids, active=True)
    if not devices.exists():
        return

    message = build_push_message(title, body, notification_type, data)

    try:
        result = devices.send_message(message)
    except Exception as e:
        logger.error(f"Failed to send {notification_type} notification: {str(e)}")
        return

    logger.info(
        f"Sent {notification_type} notification to {len(result.registration_ids_sent)} device(s) "
        f"for {len(user_ids)} user(s): {result.success_count} delivered to FCM, "
        f"{result.failure_count} rejected, "
        f"{len(result.deactivated_registration_ids)} token(s) deactivated"
    )
    if result.has_failures:
        logger.error(
            f"FCM rejected {result.failure_count} of {len(result.registration_ids_sent)} "
            f"{notification_type} message(s): {result.failed_exceptions}"
        )
