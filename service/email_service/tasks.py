import logging

from procrastinate.contrib.django import app

from email_service import utils as email_utils

logger = logging.getLogger(__name__)


@app.task(name="email_service.send_email_notification")
def send_email_notification(user_ids, subject, html):
    logger.info(f"Running send_email_notification task: {subject}")
    email_utils.send_email_to_users(
        user_ids=user_ids,
        subject=subject,
        html=html,
    )
