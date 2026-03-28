import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from user_profile.models import UserProfile

User = get_user_model()

login_viewname = "email-login"


@pytest.mark.django_db
class TestEmailLogin:
    def test_successful_login(self, unauthenticated_client):
        user = User.objects.create_user(
            username="player@example.com",
            email="player@example.com",
            password="strongpass123",
            is_active=True,
        )
        UserProfile.objects.create(user=user, name="Test Player")

        url = reverse(login_viewname)
        response = unauthenticated_client.post(
            url,
            {"email": "player@example.com", "password": "strongpass123"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == user.id
        assert response.data["email"] == "player@example.com"
        assert response.data["name"] == "Test Player"
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_wrong_password_returns_401(self, unauthenticated_client):
        User.objects.create_user(
            username="player@example.com",
            email="player@example.com",
            password="strongpass123",
            is_active=True,
        )

        url = reverse(login_viewname)
        response = unauthenticated_client.post(
            url,
            {"email": "player@example.com", "password": "wrongpass123"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in str(response.data)

    def test_nonexistent_email_returns_401(self, unauthenticated_client):
        url = reverse(login_viewname)
        response = unauthenticated_client.post(
            url,
            {"email": "nobody@example.com", "password": "anypass123"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in str(response.data)

    def test_unverified_account_returns_401(self, unauthenticated_client):
        User.objects.create_user(
            username="unverified@example.com",
            email="unverified@example.com",
            password="strongpass123",
            is_active=False,
        )

        url = reverse(login_viewname)
        response = unauthenticated_client.post(
            url,
            {"email": "unverified@example.com", "password": "strongpass123"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not verified" in str(response.data)
        assert "check your email" in str(response.data).lower()
