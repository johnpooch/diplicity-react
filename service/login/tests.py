import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from google.auth.exceptions import GoogleAuthError
from user_profile.models import UserProfile

User = get_user_model()

viewname = "auth"


@pytest.mark.django_db
def test_invalid_request_body_returns_400(unauthenticated_client):
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_google_auth_verification_error_returns_401(unauthenticated_client, mock_google_auth):
    mock_google_auth.side_effect = GoogleAuthError("Mocked GoogleAuthError")
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_google_auth_value_error_returns_401(unauthenticated_client, mock_google_auth):
    mock_google_auth.side_effect = ValueError("Mocked ValueError")
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_google_auth_wrong_issuer_returns_401(unauthenticated_client, mock_google_auth):
    mock_google_auth.return_value = {"iss": "wrong_issuer", "aud": "web-client-id"}
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_creates_new_user_if_no_existing_user(unauthenticated_client, mock_google_auth, mock_refresh_token):
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert "refresh_token" in response.data

    user_profile = UserProfile.objects.get(user__email="test@example.com")
    assert user_profile.picture == "http://example.com/picture.jpg"
    assert user_profile.name == "Test User"


@pytest.mark.django_db
def test_existing_user_sign_in(unauthenticated_client, mock_google_auth, mock_refresh_token):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    user_profile = UserProfile.objects.create(
        user=user,
        name="Test User",
        picture="http://example.com/picture.jpg",
    )

    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert "refresh_token" in response.data

    user_profile.refresh_from_db()
    assert user_profile.picture == "http://example.com/picture.jpg"
    assert user_profile.name == "Test User"


@pytest.mark.django_db
def test_creates_new_user_with_null_picture(unauthenticated_client, mock_google_auth_without_picture, mock_refresh_token):
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert "refresh_token" in response.data

    user_profile = UserProfile.objects.get(user__email="test@example.com")
    assert user_profile.picture is None
    assert user_profile.name == "Test User"


@pytest.mark.django_db
def test_updates_existing_user_picture_to_null(unauthenticated_client, mock_google_auth_without_picture, mock_refresh_token):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    user_profile = UserProfile.objects.create(
        user=user,
        name="Test User",
        picture="http://example.com/picture.jpg",
    )

    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert "refresh_token" in response.data

    user_profile.refresh_from_db()
    assert user_profile.picture is None
    assert user_profile.name == "Test User"
    assert user_profile.user.email == "test@example.com"


@pytest.mark.django_db
def test_ios_client_id_audience_accepted(unauthenticated_client, mock_google_auth, mock_refresh_token):
    mock_google_auth.return_value = {
        "iss": "accounts.google.com",
        "aud": "ios-client-id",
        "email": "test@example.com",
        "name": "iOS User",
        "picture": "http://example.com/ios_picture.jpg",
    }
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "ios_token"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert "refresh_token" in response.data


@pytest.mark.django_db
def test_unknown_audience_rejected(unauthenticated_client, mock_google_auth):
    mock_google_auth.return_value = {
        "iss": "accounts.google.com",
        "aud": "unknown-client-id",
        "email": "test@example.com",
        "name": "Test User",
    }
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "bad_token"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
