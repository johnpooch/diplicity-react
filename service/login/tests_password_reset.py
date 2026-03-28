from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status

User = get_user_model()

password_reset_viewname = "password-reset"


@pytest.mark.django_db
class TestPasswordReset:
    def test_sends_reset_email_for_valid_user(self, unauthenticated_client, mock_send_email):
        User.objects.create_user(
            username="player@example.com",
            email="player@example.com",
            password="strongpass123",
            is_active=True,
        )

        url = reverse(password_reset_viewname)
        response = unauthenticated_client.post(
            url,
            {"email": "player@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]
        assert call_kwargs["to"] == "player@example.com"
        assert "reset" in call_kwargs["subject"].lower()
        assert "reset-password?uid=" in call_kwargs["html"]

    def test_nonexistent_email_returns_200_without_sending(self, unauthenticated_client, mock_send_email):
        url = reverse(password_reset_viewname)
        response = unauthenticated_client.post(
            url,
            {"email": "nobody@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_send_email.assert_not_called()


@pytest.mark.django_db
class TestPasswordResetConfirm:
    def test_valid_token_sets_new_password(self, unauthenticated_client):
        user = User.objects.create_user(
            username="reset@example.com",
            email="reset@example.com",
            password="oldpass123",
            is_active=True,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = unauthenticated_client.post(
            "/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "newpass456", "confirm_password": "newpass456"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("newpass456")

    def test_invalid_token_returns_400(self, unauthenticated_client):
        user = User.objects.create_user(
            username="invalid@example.com",
            email="invalid@example.com",
            password="oldpass123",
            is_active=True,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = unauthenticated_client.post(
            "/auth/password-reset/confirm/",
            {"uid": uid, "token": "bad-token", "new_password": "newpass456", "confirm_password": "newpass456"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid or expired" in str(response.json()).lower()
        user.refresh_from_db()
        assert user.check_password("oldpass123")

    def test_invalid_uid_returns_400(self, unauthenticated_client):
        response = unauthenticated_client.post(
            "/auth/password-reset/confirm/",
            {"uid": "baduid", "token": "bad-token", "new_password": "newpass456", "confirm_password": "newpass456"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mismatched_passwords_returns_400(self, unauthenticated_client):
        user = User.objects.create_user(
            username="mismatch@example.com",
            email="mismatch@example.com",
            password="oldpass123",
            is_active=True,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = unauthenticated_client.post(
            "/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "newpass456", "confirm_password": "different789"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "do not match" in str(response.json()).lower()
        user.refresh_from_db()
        assert user.check_password("oldpass123")
