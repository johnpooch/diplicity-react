import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from user_profile.models import UserProfile

User = get_user_model()

register_viewname = "register"
verify_viewname = "verify-email"


@pytest.mark.django_db
class TestRegister:
    def test_successful_registration(self, unauthenticated_client, mock_send_email):
        url = reverse(register_viewname)
        response = unauthenticated_client.post(
            url,
            {
                "email": "new@example.com",
                "password": "strongpass123",
                "display_name": "New Player",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(email="new@example.com")
        assert user.is_active is False
        assert user.check_password("strongpass123")

        profile = UserProfile.objects.get(user=user)
        assert profile.name == "New Player"

    def test_duplicate_email_returns_400(self, unauthenticated_client, mock_send_email):
        User.objects.create_user(
            username="existing",
            email="taken@example.com",
            password="somepass123",
        )

        url = reverse(register_viewname)
        response = unauthenticated_client.post(
            url,
            {
                "email": "taken@example.com",
                "password": "strongpass123",
                "display_name": "Another Player",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in str(response.data["email"])

    def test_short_password_returns_400(self, unauthenticated_client, mock_send_email):
        url = reverse(register_viewname)
        response = unauthenticated_client.post(
            url,
            {
                "email": "short@example.com",
                "password": "short",
                "display_name": "Short Pass",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_registration_sends_verification_email(self, unauthenticated_client, mock_send_email):
        url = reverse(register_viewname)
        unauthenticated_client.post(
            url,
            {
                "email": "verify@example.com",
                "password": "strongpass123",
                "display_name": "Email Test",
            },
            format="json",
        )

        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]
        assert call_kwargs["to"] == "verify@example.com"
        assert call_kwargs["subject"] == "Verify your Diplicity account"
        assert "verify-email" in call_kwargs["html"]


@pytest.mark.django_db
class TestVerifyEmail:
    def test_valid_token_activates_user(self, unauthenticated_client):
        user = User.objects.create_user(
            username="inactive@example.com",
            email="inactive@example.com",
            password="testpass123",
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse(verify_viewname)
        response = unauthenticated_client.post(
            url,
            {"uid": uid, "token": token},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is True

    def test_invalid_token_returns_400(self, unauthenticated_client):
        user = User.objects.create_user(
            username="inactive2@example.com",
            email="inactive2@example.com",
            password="testpass123",
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        url = reverse(verify_viewname)
        response = unauthenticated_client.post(
            url,
            {"uid": uid, "token": "bad-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.is_active is False
