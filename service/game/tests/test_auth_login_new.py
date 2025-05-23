import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from google.auth.exceptions import GoogleAuthError
from game import models

User = get_user_model()

viewname = "auth-login"

@pytest.mark.django_db
def test_invalid_request_body_returns_400(unauthenticated_client):
    """
    Test that an invalid request body returns 400.
    """
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_google_auth_verification_error_returns_401(unauthenticated_client, mock_google_auth):
    """
    Test that Google auth verification error returns 401.
    """
    mock_google_auth.side_effect = GoogleAuthError("Mocked GoogleAuthError")
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_google_auth_value_error_returns_401(unauthenticated_client, mock_google_auth):
    """
    Test that Google auth value error returns 401.
    """
    mock_google_auth.side_effect = ValueError("Mocked ValueError")
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_google_auth_wrong_issuer_returns_401(unauthenticated_client, mock_google_auth):
    """
    Test that Google auth with wrong issuer returns 401.
    """
    mock_google_auth.return_value = {"iss": "wrong_issuer"}
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_creates_new_user_if_no_existing_user(unauthenticated_client, mock_google_auth, mock_refresh_token):
    """
    Test that a new user is created if no existing user is found.
    """
    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data
    assert "refresh_token" in response.data

    user_profile = models.UserProfile.objects.get(user__email="test@example.com")
    assert user_profile.picture == "http://example.com/picture.jpg"
    assert user_profile.name == "Test User"

@pytest.mark.django_db
def test_existing_user_sign_in(unauthenticated_client, mock_google_auth, mock_refresh_token):
    """
    Test that an existing user can sign in.
    """
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    user_profile = models.UserProfile.objects.create(
        user=user,
        name="Test User",
        picture="http://example.com/picture.jpg",
    )

    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data
    assert "refresh_token" in response.data

    user_profile.refresh_from_db()
    assert user_profile.picture == "http://example.com/picture.jpg"
    assert user_profile.name == "Test User" 