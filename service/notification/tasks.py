import logging

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
