import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10


def post_message(content):
    if not settings.DISCORD_MODERATION_WEBHOOK_URL:
        logger.warning(
            "Skipped Discord message: DISCORD_MODERATION_WEBHOOK_URL is not set"
        )
        return
    response = requests.post(
        settings.DISCORD_MODERATION_WEBHOOK_URL,
        json={"content": content, "allowed_mentions": {"parse": []}},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
