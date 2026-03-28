from unittest.mock import patch

import pytest
from django.test import override_settings


class TestSendEmail:
    @patch("email_service.utils.resend")
    def test_sends_email_with_correct_params(self, mock_resend):
        from email_service.utils import send_email

        send_email(
            to="player@example.com",
            subject="Welcome to Diplicity",
            html="<h1>Welcome!</h1>",
        )

        mock_resend.Emails.send.assert_called_once_with(
            {
                "from": "Diplicity <noreply@diplicity.com>",
                "to": ["player@example.com"],
                "subject": "Welcome to Diplicity",
                "html": "<h1>Welcome!</h1>",
            }
        )

    @override_settings(RESEND_API_KEY="test-api-key-123")
    @patch("email_service.utils.resend")
    def test_sets_api_key_from_settings(self, mock_resend):
        from email_service.utils import send_email

        send_email(to="a@b.com", subject="Test", html="<p>Hi</p>")

        assert mock_resend.api_key == "test-api-key-123"

    @patch("email_service.utils.resend")
    def test_handles_resend_api_error(self, mock_resend):
        from email_service.utils import send_email

        mock_resend.Emails.send.side_effect = Exception("Resend API error")

        send_email(to="a@b.com", subject="Test", html="<p>Hi</p>")
