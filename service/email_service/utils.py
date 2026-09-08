import logging

import resend
import sentry_sdk
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

FROM_ADDRESS = "Diplicity <noreply@diplicity.com>"
EMAIL_DISABLED_ERROR = "email notifications disabled"
NO_EMAIL_ADDRESS_ERROR = "no email address"


def send_email(to, subject, html):
    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send(
        {
            "from": FROM_ADDRESS,
            "to": [to],
            "subject": subject,
            "html": html,
        }
    )
    logger.info(f"Sent email to {to}: {subject}")


def send_email_best_effort(to, subject, html):
    try:
        send_email(to=to, subject=subject, html=html)
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        sentry_sdk.capture_exception(e)


def send_email_to_users(user_ids, subject, html):
    if not user_ids:
        return {}

    addresses = dict(
        User.objects.filter(
            id__in=user_ids,
            profile__email_notifications_enabled=True,
        ).values_list("id", "email")
    )

    results = {}
    for user_id in user_ids:
        if user_id not in addresses:
            results[user_id] = EMAIL_DISABLED_ERROR
        elif not addresses[user_id]:
            results[user_id] = NO_EMAIL_ADDRESS_ERROR
        else:
            try:
                send_email(to=addresses[user_id], subject=subject, html=html)
                results[user_id] = None
            except Exception as e:
                logger.error(f"Failed to send email to {addresses[user_id]}: {e}")
                results[user_id] = str(e)
    return results
