import logging

import resend
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

FROM_ADDRESS = "Diplicity <noreply@diplicity.com>"


def send_email(to, subject, html):
    resend.api_key = settings.RESEND_API_KEY
    try:
        resend.Emails.send(
            {
                "from": FROM_ADDRESS,
                "to": [to],
                "subject": subject,
                "html": html,
            }
        )
        logger.info(f"Sent email to {to}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")


def send_email_to_users(user_ids, subject, html):
    if not user_ids:
        return

    users = User.objects.filter(
        id__in=user_ids,
        profile__email_notifications_enabled=True,
    ).values_list("email", flat=True)

    for email in users:
        if email:
            send_email(to=email, subject=subject, html=html)
