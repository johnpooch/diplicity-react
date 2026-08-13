import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.management import call_command
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from google.auth.exceptions import GoogleAuthError
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from user_profile.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
class TestGoogleAuthView:
    def test_invalid_request_body_returns_400(self, unauthenticated_client):
        url = reverse("auth")
        response = unauthenticated_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_google_auth_verification_error_returns_401(self, unauthenticated_client, mock_google_auth):
        mock_google_auth.side_effect = GoogleAuthError("Mocked GoogleAuthError")
        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_google_auth_value_error_returns_401(self, unauthenticated_client, mock_google_auth):
        mock_google_auth.side_effect = ValueError("Mocked ValueError")
        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_google_auth_wrong_issuer_returns_401(self, unauthenticated_client, mock_google_auth):
        mock_google_auth.return_value = {"iss": "wrong_issuer", "aud": "web-client-id"}
        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_creates_new_user_if_no_existing_user(self, unauthenticated_client, mock_google_auth, mock_refresh_token):
        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access_token" in response.data
        assert "refresh_token" in response.data

        user_profile = UserProfile.objects.get(user__email="test@example.com")
        assert user_profile.picture == "http://example.com/picture.jpg"
        assert user_profile.name == "Test User"

    def test_existing_user_sign_in(self, unauthenticated_client, mock_google_auth, mock_refresh_token):
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

        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access_token" in response.data
        assert "refresh_token" in response.data

        user_profile.refresh_from_db()
        assert user_profile.picture == "http://example.com/picture.jpg"
        assert user_profile.name == "Custom Name"

    def test_creates_new_user_with_null_picture(
        self, unauthenticated_client, mock_google_auth_without_picture, mock_refresh_token
    ):
        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access_token" in response.data
        assert "refresh_token" in response.data

        user_profile = UserProfile.objects.get(user__email="test@example.com")
        assert user_profile.picture is None
        assert user_profile.name == "Test User"

    def test_updates_existing_user_picture_to_null(
        self, unauthenticated_client, mock_google_auth_without_picture, mock_refresh_token
    ):
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

        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access_token" in response.data
        assert "refresh_token" in response.data

        user_profile.refresh_from_db()
        assert user_profile.picture is None
        assert user_profile.name == "Test User"
        assert user_profile.user.email == "test@example.com"

    def test_creates_new_user_without_name(
        self, unauthenticated_client, mock_google_auth_without_name, mock_refresh_token
    ):
        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        user_profile = UserProfile.objects.get(user__email="test@example.com")
        assert user_profile.name == "test"
        assert user_profile.user.username == "test"

    def test_existing_user_sign_in_without_name(
        self, unauthenticated_client, mock_google_auth_without_name, mock_refresh_token
    ):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        user_profile = UserProfile.objects.create(user=user, name="Custom Name")

        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        user_profile.refresh_from_db()
        assert user_profile.name == "Custom Name"
        assert User.objects.filter(email="test@example.com").count() == 1

    def test_ios_client_id_audience_accepted(self, unauthenticated_client, mock_google_auth, mock_refresh_token):
        mock_google_auth.return_value = {
            "iss": "accounts.google.com",
            "aud": "ios-client-id",
            "email": "test@example.com",
            "name": "iOS User",
            "picture": "http://example.com/ios_picture.jpg",
        }
        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "ios_token"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_google_oauth_links_to_existing_email_password_account(
        self, unauthenticated_client, mock_google_auth, mock_refresh_token
    ):
        user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="securepass123",
            is_active=False,
        )
        UserProfile.objects.create(user=user, name="Original Name")

        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == user.id

        user.refresh_from_db()
        assert user.is_active is True

        user_profile = UserProfile.objects.get(user=user)
        assert user_profile.name == "Original Name"
        assert user_profile.picture == "http://example.com/picture.jpg"

        assert User.objects.filter(email="test@example.com").count() == 1

    def test_email_password_login_works_after_google_linking(
        self, unauthenticated_client, mock_google_auth, mock_refresh_token
    ):
        user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="securepass123",
            is_active=False,
        )
        UserProfile.objects.create(user=user, name="Original Name")

        url = reverse("auth")
        unauthenticated_client.post(url, {"id_token": "valid_token"}, format="json")

        email_login_url = reverse("email-login")
        response = unauthenticated_client.post(
            email_login_url,
            {"email": "test@example.com", "password": "securepass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == user.id

    def test_unknown_audience_rejected(self, unauthenticated_client, mock_google_auth):
        mock_google_auth.return_value = {
            "iss": "accounts.google.com",
            "aud": "unknown-client-id",
            "email": "test@example.com",
            "name": "Test User",
        }
        url = reverse("auth")
        response = unauthenticated_client.post(url, {"id_token": "bad_token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAppleAuthView:
    def test_missing_id_token_returns_400(self, unauthenticated_client):
        url = reverse("apple-auth")
        response = unauthenticated_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_creates_new_user_with_name(self, unauthenticated_client, mock_apple_auth, mock_refresh_token):
        url = reverse("apple-auth")
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

    def test_creates_new_user_without_name(self, unauthenticated_client, mock_apple_auth, mock_refresh_token):
        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url, {"id_token": "apple_token"}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

        user_profile = UserProfile.objects.get(user__email="apple@example.com")
        assert user_profile.name == "apple"

    def test_existing_user_sign_in(self, unauthenticated_client, mock_apple_auth, mock_refresh_token):
        user = User.objects.create_user(
            username="appleuser", email="apple@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="Existing Name")

        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url, {"id_token": "apple_token"}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == user.id

        user_profile = UserProfile.objects.get(user=user)
        assert user_profile.name == "Existing Name"

    def test_links_to_existing_inactive_account(self, unauthenticated_client, mock_apple_auth, mock_refresh_token):
        user = User.objects.create_user(
            username="apple@example.com",
            email="apple@example.com",
            password="securepass123",
            is_active=False,
        )
        UserProfile.objects.create(user=user, name="Original Name")

        url = reverse("apple-auth")
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

    def test_relay_email_accepted(self, unauthenticated_client, mock_apple_auth_relay_email, mock_refresh_token):
        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url,
            {"id_token": "apple_token", "first_name": "Jane"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        user_profile = UserProfile.objects.get(user__email="abc123@privaterelay.appleid.com")
        assert user_profile.name == "Jane"

    def test_invalid_token_returns_401(self, unauthenticated_client, mock_apple_auth):
        mock_apple_auth.side_effect = AuthenticationFailed("Apple authentication failed")
        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url, {"id_token": "bad_token"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_returns_401(self, unauthenticated_client, mock_apple_auth):
        mock_apple_auth.side_effect = AuthenticationFailed("Apple token has expired")
        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url, {"id_token": "expired_token"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_subsequent_login_preserves_existing_profile(
        self, unauthenticated_client, mock_apple_auth, mock_refresh_token
    ):
        user = User.objects.create_user(
            username="appleuser", email="apple@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="Existing Name")

        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url, {"id_token": "apple_token"}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

        user_profile = UserProfile.objects.get(user=user)
        assert user_profile.name == "Existing Name"

    @pytest.mark.parametrize("audience", ["com.diplicity.app", "com.diplicity.web"])
    def test_native_and_web_audiences_accepted(
        self,
        settings,
        unauthenticated_client,
        patch_apple_key,
        apple_id_token_factory,
        mock_refresh_token,
        audience,
    ):
        settings.APPLE_CLIENT_ID = "com.diplicity.app"
        settings.APPLE_WEB_CLIENT_ID = "com.diplicity.web"

        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url, {"id_token": apple_id_token_factory(audience)}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "apple@example.com"

    def test_unknown_audience_rejected(
        self, settings, unauthenticated_client, patch_apple_key, apple_id_token_factory
    ):
        settings.APPLE_CLIENT_ID = "com.diplicity.app"
        settings.APPLE_WEB_CLIENT_ID = "com.diplicity.web"

        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url, {"id_token": apple_id_token_factory("com.someone.else")}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert User.objects.filter(email="apple@example.com").exists() is False

    def test_web_audience_rejected_when_unset(
        self, settings, unauthenticated_client, patch_apple_key, apple_id_token_factory
    ):
        settings.APPLE_CLIENT_ID = "com.diplicity.app"
        settings.APPLE_WEB_CLIENT_ID = None

        url = reverse("apple-auth")
        response = unauthenticated_client.post(
            url, {"id_token": apple_id_token_factory("com.diplicity.web")}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert User.objects.filter(email="apple@example.com").exists() is False


@pytest.mark.django_db
class TestEmailLoginView:
    def test_successful_login(self, unauthenticated_client):
        user = User.objects.create_user(
            username="player@example.com",
            email="player@example.com",
            password="strongpass123",
            is_active=True,
        )
        UserProfile.objects.create(user=user, name="Test Player")

        url = reverse("email-login")
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

        url = reverse("email-login")
        response = unauthenticated_client.post(
            url,
            {"email": "player@example.com", "password": "wrongpass123"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in str(response.data)

    def test_nonexistent_email_returns_401(self, unauthenticated_client):
        url = reverse("email-login")
        response = unauthenticated_client.post(
            url,
            {"email": "nobody@example.com", "password": "anypass123"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in str(response.data)

    def test_case_insensitive_email_login(self, unauthenticated_client):
        user = User.objects.create_user(
            username="Player@Example.com",
            email="Player@Example.com",
            password="strongpass123",
            is_active=True,
        )
        UserProfile.objects.create(user=user, name="Test Player")

        url = reverse("email-login")
        response = unauthenticated_client.post(
            url,
            {"email": "PLAYER@EXAMPLE.COM", "password": "strongpass123"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_unverified_account_returns_401(self, unauthenticated_client):
        User.objects.create_user(
            username="unverified@example.com",
            email="unverified@example.com",
            password="strongpass123",
            is_active=False,
        )

        url = reverse("email-login")
        response = unauthenticated_client.post(
            url,
            {"email": "unverified@example.com", "password": "strongpass123"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not verified" in str(response.data)
        assert "check your email" in str(response.data).lower()


@pytest.mark.django_db
class TestRegisterView:
    def test_successful_registration(self, unauthenticated_client, mock_send_email):
        url = reverse("register")
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

        url = reverse("register")
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

    def test_duplicate_email_message_names_google_and_apple(self, unauthenticated_client, mock_send_email):
        User.objects.create_user(
            username="existing",
            email="taken@example.com",
            password="somepass123",
        )

        url = reverse("register")
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
        assert "Google" in str(response.data["email"])
        assert "Apple" in str(response.data["email"])

    def test_duplicate_email_case_insensitive_returns_400(self, unauthenticated_client, mock_send_email):
        User.objects.create_user(
            username="existing",
            email="Taken@Example.com",
            password="somepass123",
        )

        url = reverse("register")
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
        url = reverse("register")
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
        url = reverse("register")
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
class TestVerifyEmailView:
    def test_valid_token_activates_user(self, unauthenticated_client):
        user = User.objects.create_user(
            username="inactive@example.com",
            email="inactive@example.com",
            password="testpass123",
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse("verify-email")
        response = unauthenticated_client.post(
            url,
            {"uid": uid, "token": token},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
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

        url = reverse("verify-email")
        response = unauthenticated_client.post(
            url,
            {"uid": uid, "token": "bad-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.is_active is False

    def test_invalid_uid_returns_400(self, unauthenticated_client):
        url = reverse("verify-email")
        response = unauthenticated_client.post(
            url,
            {"uid": "baduid", "token": "bad-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification link." in response.data["uid"]


@pytest.mark.django_db
class TestPasswordResetView:
    def test_sends_reset_email_for_valid_user(self, unauthenticated_client, mock_send_email):
        User.objects.create_user(
            username="player@example.com",
            email="player@example.com",
            password="strongpass123",
            is_active=True,
        )

        url = reverse("password-reset")
        response = unauthenticated_client.post(
            url,
            {"email": "player@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]
        assert call_kwargs["to"] == "player@example.com"
        assert "reset" in call_kwargs["subject"].lower()
        assert "reset-password?uid=" in call_kwargs["html"]

    def test_case_insensitive_email_sends_reset(self, unauthenticated_client, mock_send_email):
        User.objects.create_user(
            username="Player@Example.com",
            email="Player@Example.com",
            password="strongpass123",
            is_active=True,
        )

        url = reverse("password-reset")
        response = unauthenticated_client.post(
            url,
            {"email": "player@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        mock_send_email.assert_called_once()

    def test_nonexistent_email_returns_200_without_sending(self, unauthenticated_client, mock_send_email):
        url = reverse("password-reset")
        response = unauthenticated_client.post(
            url,
            {"email": "nobody@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        mock_send_email.assert_not_called()


@pytest.mark.django_db
class TestPasswordResetConfirmView:
    def test_valid_token_sets_new_password(self, unauthenticated_client):
        user = User.objects.create_user(
            username="reset@example.com",
            email="reset@example.com",
            password="oldpass123",
            is_active=True,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse("password-reset-confirm")
        response = unauthenticated_client.post(
            url,
            {"uid": uid, "token": token, "new_password": "newpass456", "confirm_password": "newpass456"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
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

        url = reverse("password-reset-confirm")
        response = unauthenticated_client.post(
            url,
            {"uid": uid, "token": "bad-token", "new_password": "newpass456", "confirm_password": "newpass456"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid or expired" in str(response.json()).lower()
        user.refresh_from_db()
        assert user.check_password("oldpass123")

    def test_invalid_uid_returns_400(self, unauthenticated_client):
        url = reverse("password-reset-confirm")
        response = unauthenticated_client.post(
            url,
            {"uid": "baduid", "token": "bad-token", "new_password": "newpass456", "confirm_password": "newpass456"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid or expired reset link." in response.data["uid"]

    def test_mismatched_passwords_returns_400(self, unauthenticated_client):
        user = User.objects.create_user(
            username="mismatch@example.com",
            email="mismatch@example.com",
            password="oldpass123",
            is_active=True,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse("password-reset-confirm")
        response = unauthenticated_client.post(
            url,
            {"uid": uid, "token": token, "new_password": "newpass456", "confirm_password": "different789"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "do not match" in str(response.json()).lower()
        user.refresh_from_db()
        assert user.check_password("oldpass123")


@pytest.mark.django_db
class TestTokenRefreshView:
    def test_token_refresh_with_deleted_user_returns_401(self, unauthenticated_client):
        user = User.objects.create_user(
            username="tobedeleted@example.com",
            email="tobedeleted@example.com",
            password="testpass123",
        )
        refresh = RefreshToken.for_user(user)
        user.delete()

        url = reverse("token-refresh")
        response = unauthenticated_client.post(
            url, {"refresh": str(refresh)}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCreateTestUserCommand:
    def test_defaults_create_active_loginable_user(self, capsys, unauthenticated_client):
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

    def test_superuser_flag_grants_admin_access(self, capsys):
        call_command("create_test_user", "--superuser")

        output = json.loads(capsys.readouterr().out)
        assert output["superuser"] is True

        user = User.objects.get(email="test@example.com")
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_is_idempotent(self, capsys):
        call_command("create_test_user")
        call_command("create_test_user")

        assert User.objects.filter(email="test@example.com").count() == 1
        assert UserProfile.objects.filter(user__email="test@example.com").count() == 1

    def test_custom_arguments(self, capsys, unauthenticated_client):
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
