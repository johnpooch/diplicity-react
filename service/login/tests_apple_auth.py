import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from user_profile.models import UserProfile

User = get_user_model()

viewname = "apple-auth"


@pytest.mark.django_db
def test_missing_id_token_returns_400(unauthenticated_client):
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_creates_new_user_with_name(unauthenticated_client, mock_apple_auth, mock_refresh_token):
    url = reverse(viewname)
    response = unauthenticated_client.post(
        url,
        {"id_token": "apple_token", "first_name": "John", "last_name": "Doe"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert "refresh_token" in response.data

    user_profile = UserProfile.objects.get(user__email="apple@example.com")
    assert user_profile.name == "John Doe"


@pytest.mark.django_db
def test_creates_new_user_without_name(unauthenticated_client, mock_apple_auth, mock_refresh_token):
    url = reverse(viewname)
    response = unauthenticated_client.post(
        url, {"id_token": "apple_token"}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED

    user_profile = UserProfile.objects.get(user__email="apple@example.com")
    assert user_profile.name == "apple"


@pytest.mark.django_db
def test_existing_user_sign_in(unauthenticated_client, mock_apple_auth, mock_refresh_token):
    user = User.objects.create_user(
        username="appleuser", email="apple@example.com", password="testpass123"
    )
    UserProfile.objects.create(user=user, name="Existing Name")

    url = reverse(viewname)
    response = unauthenticated_client.post(
        url, {"id_token": "apple_token"}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["id"] == user.id

    user_profile = UserProfile.objects.get(user=user)
    assert user_profile.name == "Existing Name"


@pytest.mark.django_db
def test_links_to_existing_inactive_account(unauthenticated_client, mock_apple_auth, mock_refresh_token):
    user = User.objects.create_user(
        username="apple@example.com",
        email="apple@example.com",
        password="securepass123",
        is_active=False,
    )
    UserProfile.objects.create(user=user, name="Original Name")

    url = reverse(viewname)
    response = unauthenticated_client.post(
        url,
        {"id_token": "apple_token", "first_name": "John", "last_name": "Doe"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["id"] == user.id

    user.refresh_from_db()
    assert user.is_active is True

    user_profile = UserProfile.objects.get(user=user)
    assert user_profile.name == "John Doe"

    assert User.objects.filter(email="apple@example.com").count() == 1


@pytest.mark.django_db
def test_relay_email_accepted(unauthenticated_client, mock_apple_auth_relay_email, mock_refresh_token):
    url = reverse(viewname)
    response = unauthenticated_client.post(
        url,
        {"id_token": "apple_token", "first_name": "Jane"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    user_profile = UserProfile.objects.get(user__email="abc123@privaterelay.appleid.com")
    assert user_profile.name == "Jane"


@pytest.mark.django_db
def test_invalid_token_returns_401(unauthenticated_client, mock_apple_auth):
    from rest_framework.exceptions import AuthenticationFailed
    mock_apple_auth.side_effect = AuthenticationFailed("Apple authentication failed")
    url = reverse(viewname)
    response = unauthenticated_client.post(
        url, {"id_token": "bad_token"}, format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_expired_token_returns_401(unauthenticated_client, mock_apple_auth):
    from rest_framework.exceptions import AuthenticationFailed
    mock_apple_auth.side_effect = AuthenticationFailed("Apple token has expired")
    url = reverse(viewname)
    response = unauthenticated_client.post(
        url, {"id_token": "expired_token"}, format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_subsequent_login_preserves_existing_profile(
    unauthenticated_client, mock_apple_auth, mock_refresh_token
):
    user = User.objects.create_user(
        username="appleuser", email="apple@example.com", password="testpass123"
    )
    UserProfile.objects.create(user=user, name="Existing Name")

    url = reverse(viewname)
    response = unauthenticated_client.post(
        url, {"id_token": "apple_token"}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED

    user_profile = UserProfile.objects.get(user=user)
    assert user_profile.name == "Existing Name"
