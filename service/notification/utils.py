import logging
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

PUSH_TTL = timedelta(hours=1)
FIREBASE_UNCONFIGURED_ERROR = "firebase is not configured"
NO_ACTIVE_DEVICE_ERROR = "no active device"


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


def push_results_by_user(user_ids, tokens_by_user, result):
    rejections = {
        registration_id: str(exception)
        for registration_id, exception in zip(result.failed_registration_ids, result.failed_exceptions)
    }
    results = {}
    for user_id in user_ids:
        registration_ids = tokens_by_user.get(user_id, [])
        if not registration_ids:
            results[user_id] = NO_ACTIVE_DEVICE_ERROR
            continue
        reasons = [rejections[r] for r in registration_ids if r in rejections]
        results[user_id] = reasons[0] if len(reasons) == len(registration_ids) else None
    return results


def send_notification_to_users(user_ids, title, body, notification_type, data=None):
    if not user_ids:
        return {}

    if not getattr(settings, "FIREBASE_APP", None):
        return {user_id: FIREBASE_UNCONFIGURED_ERROR for user_id in user_ids}

    from fcm_django.models import FCMDevice

    devices = FCMDevice.objects.filter(user_id__in=user_ids, active=True)
    tokens_by_user = defaultdict(list)
    for registration_id, user_id in devices.values_list("registration_id", "user_id"):
        tokens_by_user[user_id].append(registration_id)

    if not tokens_by_user:
        return {user_id: NO_ACTIVE_DEVICE_ERROR for user_id in user_ids}

    message = build_push_message(title, body, notification_type, data)

    try:
        result = devices.send_message(message)
    except Exception as e:
        logger.error(f"Failed to send {notification_type} notification: {str(e)}")
        return {user_id: str(e) if user_id in tokens_by_user else NO_ACTIVE_DEVICE_ERROR for user_id in user_ids}

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

    return push_results_by_user(user_ids, tokens_by_user, result)
