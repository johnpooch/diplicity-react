import json

import pytest
from django.core.management import call_command
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
        name="Custom Name",
        picture="http://example.com/picture.jpg",
    )

    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert "refresh_token" in response.data

    user_profile.refresh_from_db()
    assert user_profile.picture == "http://example.com/picture.jpg"
    assert user_profile.name == "Custom Name"


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
def test_google_oauth_links_to_existing_email_password_account(
    unauthenticated_client, mock_google_auth, mock_refresh_token
):
    user = User.objects.create_user(
        username="test@example.com",
        email="test@example.com",
        password="securepass123",
        is_active=False,
    )
    UserProfile.objects.create(user=user, name="Original Name")

    url = reverse(viewname)
    response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["id"] == user.id

    user.refresh_from_db()
    assert user.is_active is True

    user_profile = UserProfile.objects.get(user=user)
    assert user_profile.name == "Original Name"
    assert user_profile.picture == "http://example.com/picture.jpg"

    assert User.objects.filter(email="test@example.com").count() == 1


@pytest.mark.django_db
def test_email_password_login_works_after_google_linking(
    unauthenticated_client, mock_google_auth, mock_refresh_token
):
    user = User.objects.create_user(
        username="test@example.com",
        email="test@example.com",
        password="securepass123",
        is_active=False,
    )
    UserProfile.objects.create(user=user, name="Original Name")

    url = reverse(viewname)
    unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")

    email_login_url = reverse("email-login")
    response = unauthenticated_client.post(
        email_login_url,
        {"email": "test@example.com", "password": "securepass123"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["id"] == user.id


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


@pytest.mark.django_db
def test_create_test_user_defaults_create_active_loginable_user(capsys, unauthenticated_client):
    call_command("create_test_user")

    output = json.loads(capsys.readouterr().out)
    assert output["email"] == "test@example.com"
    assert output["password"] == "password"
    assert output["superuser"] is False

    user = User.objects.get(email="test@example.com")
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert UserProfile.objects.get(user=user).name == "Test User"

    response = unauthenticated_client.post(
        reverse("email-login"),
        {"email": "test@example.com", "password": "password"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_test_user_superuser_flag_grants_admin_access(capsys):
    call_command("create_test_user", "--superuser")

    output = json.loads(capsys.readouterr().out)
    assert output["superuser"] is True

    user = User.objects.get(email="test@example.com")
    assert user.is_staff is True
    assert user.is_superuser is True


@pytest.mark.django_db
def test_create_test_user_is_idempotent(capsys):
    call_command("create_test_user")
    call_command("create_test_user")

    assert User.objects.filter(email="test@example.com").count() == 1
    assert UserProfile.objects.filter(user__email="test@example.com").count() == 1


@pytest.mark.django_db
def test_create_test_user_custom_arguments(capsys, unauthenticated_client):
    call_command(
        "create_test_user",
        "--email",
        "custom@example.com",
        "--name",
        "Custom Name",
        "--password",
        "custompass123",
    )

    user = User.objects.get(email="custom@example.com")
    assert user.username == "custom"
    assert UserProfile.objects.get(user=user).name == "Custom Name"

    response = unauthenticated_client.post(
        reverse("email-login"),
        {"email": "custom@example.com", "password": "custompass123"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
