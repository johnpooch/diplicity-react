from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from email_service.utils import EMAIL_DISABLED_ERROR, NO_EMAIL_ADDRESS_ERROR
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
    def test_resend_api_error_is_raised(self, mock_resend):
        from email_service.utils import send_email

        mock_resend.Emails.send.side_effect = Exception("Resend API error")

        with pytest.raises(Exception, match="Resend API error"):
            send_email(to="a@b.com", subject="Test", html="<p>Hi</p>")


class TestSendEmailBestEffort:
    @patch("email_service.utils.sentry_sdk")
    @patch("email_service.utils.resend")
    def test_sends_email_with_correct_params(self, mock_resend, mock_sentry):
        from email_service.utils import send_email_best_effort

        send_email_best_effort(to="a@b.com", subject="Test", html="<p>Hi</p>")

        mock_resend.Emails.send.assert_called_once()
        mock_sentry.capture_exception.assert_not_called()

    @patch("email_service.utils.sentry_sdk")
    @patch("email_service.utils.resend")
    def test_resend_api_error_is_reported_not_raised(self, mock_resend, mock_sentry):
        from email_service.utils import send_email_best_effort

        mock_resend.Emails.send.side_effect = Exception("Resend API error")

        send_email_best_effort(to="a@b.com", subject="Test", html="<p>Hi</p>")

        mock_sentry.capture_exception.assert_called_once()


class TestSendEmailToUsers:

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_sends_to_users_with_email_notifications_enabled(self, mock_resend):
        from email_service.utils import send_email_to_users

        user = User.objects.create_user(username="enabled", email="enabled@example.com", password="pass")
        UserProfile.objects.create(user=user, name="Enabled User", email_notifications_enabled=True)

        results = send_email_to_users(
            user_ids=[user.id],
            subject="Test",
            html="<p>Hello</p>",
        )

        mock_resend.Emails.send.assert_called_once()
        assert mock_resend.Emails.send.call_args[0][0]["to"] == ["enabled@example.com"]
        assert results == {user.id: None}

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_skips_users_with_email_notifications_disabled(self, mock_resend):
        from email_service.utils import send_email_to_users

        user = User.objects.create_user(username="disabled", email="disabled@example.com", password="pass")
        UserProfile.objects.create(user=user, name="Disabled User", email_notifications_enabled=False)

        results = send_email_to_users(
            user_ids=[user.id],
            subject="Test",
            html="<p>Hello</p>",
        )

        mock_resend.Emails.send.assert_not_called()
        assert results == {user.id: EMAIL_DISABLED_ERROR}

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_reports_user_without_an_email_address(self, mock_resend):
        from email_service.utils import send_email_to_users

        user = User.objects.create_user(username="blank", email="", password="pass")
        UserProfile.objects.create(user=user, name="Blank User", email_notifications_enabled=True)

        results = send_email_to_users(user_ids=[user.id], subject="Test", html="<p>Hello</p>")

        mock_resend.Emails.send.assert_not_called()
        assert results == {user.id: NO_EMAIL_ADDRESS_ERROR}

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_reports_resend_error_per_recipient(self, mock_resend):
        from email_service.utils import send_email_to_users

        one = User.objects.create_user(username="one", email="one@example.com", password="pass")
        UserProfile.objects.create(user=one, name="One", email_notifications_enabled=True)
        two = User.objects.create_user(username="two", email="two@example.com", password="pass")
        UserProfile.objects.create(user=two, name="Two", email_notifications_enabled=True)
        mock_resend.Emails.send.side_effect = [Exception("Resend API error"), None]

        results = send_email_to_users(user_ids=[one.id, two.id], subject="Test", html="<p>Hello</p>")

        assert results == {one.id: "Resend API error", two.id: None}

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_filters_mixed_users(self, mock_resend):
        from email_service.utils import send_email_to_users

        user_on = User.objects.create_user(username="on", email="on@example.com", password="pass")
        UserProfile.objects.create(user=user_on, name="On User", email_notifications_enabled=True)

        user_off = User.objects.create_user(username="off", email="off@example.com", password="pass")
        UserProfile.objects.create(user=user_off, name="Off User", email_notifications_enabled=False)

        results = send_email_to_users(
            user_ids=[user_on.id, user_off.id],
            subject="Test",
            html="<p>Hello</p>",
        )

        assert results == {user_on.id: None, user_off.id: EMAIL_DISABLED_ERROR}

        assert mock_resend.Emails.send.call_count == 1
        assert mock_resend.Emails.send.call_args[0][0]["to"] == ["on@example.com"]

    @pytest.mark.django_db
    @patch("email_service.utils.resend")
    def test_handles_empty_user_ids(self, mock_resend):
        from email_service.utils import send_email_to_users

        results = send_email_to_users(user_ids=[], subject="Test", html="<p>Hello</p>")

        mock_resend.Emails.send.assert_not_called()
        assert results == {}


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
        assert 'href="None"' not in html
        assert "View Game" not in html
