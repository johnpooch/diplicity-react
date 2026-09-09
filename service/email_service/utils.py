import logging

import resend
from django.conf import settings

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
