from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from user_profile.models import UserProfile

User = get_user_model()


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


class TestSendEmailToUsers:

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_sends_to_users_with_email_notifications_enabled(self, mock_resend):
        from email_service.utils import send_email_to_users

        user = User.objects.create_user(username="enabled", email="enabled@example.com", password="pass")
        UserProfile.objects.create(user=user, name="Enabled User", email_notifications_enabled=True)

        send_email_to_users(
            user_ids=[user.id],
            subject="Test",
            html="<p>Hello</p>",
        )

        mock_resend.Emails.send.assert_called_once()
        assert mock_resend.Emails.send.call_args[0][0]["to"] == ["enabled@example.com"]

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_skips_users_with_email_notifications_disabled(self, mock_resend):
        from email_service.utils import send_email_to_users

        user = User.objects.create_user(username="disabled", email="disabled@example.com", password="pass")
        UserProfile.objects.create(user=user, name="Disabled User", email_notifications_enabled=False)

        send_email_to_users(
            user_ids=[user.id],
            subject="Test",
            html="<p>Hello</p>",
        )

        mock_resend.Emails.send.assert_not_called()

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_filters_mixed_users(self, mock_resend):
        from email_service.utils import send_email_to_users

        user_on = User.objects.create_user(username="on", email="on@example.com", password="pass")
        UserProfile.objects.create(user=user_on, name="On User", email_notifications_enabled=True)

        user_off = User.objects.create_user(username="off", email="off@example.com", password="pass")
        UserProfile.objects.create(user=user_off, name="Off User", email_notifications_enabled=False)

        send_email_to_users(
            user_ids=[user_on.id, user_off.id],
            subject="Test",
            html="<p>Hello</p>",
        )

        assert mock_resend.Emails.send.call_count == 1
        assert mock_resend.Emails.send.call_args[0][0]["to"] == ["on@example.com"]

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_handles_empty_user_ids(self, mock_resend):
        from email_service.utils import send_email_to_users

        send_email_to_users(user_ids=[], subject="Test", html="<p>Hello</p>")

        mock_resend.Emails.send.assert_not_called()


class TestNotificationEmailTemplate:

    def test_includes_title_and_body(self):
        from email_service.templates import notification_email

        html = notification_email(title="Game Started", body="Your game has begun.")
        assert "Game Started" in html
        assert "Your game has begun." in html

    def test_includes_link_when_provided(self):
        from email_service.templates import notification_email

        html = notification_email(
            title="Test",
            body="Test body",
            link="https://diplicity.com/game/123",
            link_text="View Game",
        )
        assert "https://diplicity.com/game/123" in html
        assert "View Game" in html

    def test_omits_link_section_when_no_link(self):
        from email_service.templates import notification_email

        html = notification_email(title="Test", body="Test body")
        assert "btn-a" not in html
