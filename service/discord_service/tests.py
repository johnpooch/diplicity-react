from unittest.mock import patch

import pytest
import requests
from django.test import override_settings

from discord_service.tasks import post
from discord_service.utils import post_message

WEBHOOK_URL = "https://discord.com/api/webhooks/1/token"


class TestPostMessage:
    @override_settings(DISCORD_MODERATION_WEBHOOK_URL=WEBHOOK_URL)
    @patch("discord_service.utils.requests.post")
    def test_posts_content_without_mentions(self, mock_post):
        post_message("New report")

        mock_post.assert_called_once_with(
            WEBHOOK_URL,
            json={"content": "New report", "allowed_mentions": {"parse": []}},
            timeout=10,
        )

    @override_settings(DISCORD_MODERATION_WEBHOOK_URL=WEBHOOK_URL)
    @patch("discord_service.utils.requests.post")
    def test_raises_on_http_error(self, mock_post):
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError()

        with pytest.raises(requests.HTTPError):
            post_message("New report")

    @override_settings(DISCORD_MODERATION_WEBHOOK_URL="")
    @patch("discord_service.utils.requests.post")
    def test_skips_without_a_webhook_url(self, mock_post):
        post_message("New report")

        mock_post.assert_not_called()


class TestPostTask:
    @override_settings(DISCORD_MODERATION_WEBHOOK_URL=WEBHOOK_URL)
    @patch("discord_service.utils.requests.post")
    def test_posts_content(self, mock_post):
        post(content="New report")

        assert mock_post.call_args.kwargs["json"]["content"] == "New report"
