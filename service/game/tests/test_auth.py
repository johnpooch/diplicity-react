from django.urls import reverse
from unittest.mock import patch
from google.auth.exceptions import GoogleAuthError
from rest_framework import status
from .base import BaseTestCase
from game.models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()


class TestAuthLogin(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("auth-login")

        # Mock Google ID token verification
        self.google_patcher = patch(
            "game.services.auth_service.google_id_token.verify_oauth2_token"
        )
        self.mock_verify_oauth2_token = self.google_patcher.start()
        self.addCleanup(self.google_patcher.stop)
        self.mock_verify_oauth2_token.return_value = {
            "iss": "accounts.google.com",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/picture.jpg",
        }

        # Mock token generation
        self.token_patcher = patch("game.services.auth_service.RefreshToken.for_user")
        self.mock_refresh_token = self.token_patcher.start()
        self.addCleanup(self.token_patcher.stop)
        self.mock_refresh_token.return_value = type(
            "MockRefreshToken",
            (object,),
            {
                "access_token": "access_token",
                "__str__": lambda self: "refresh_token",
            },
        )()

    def create_request(self, payload):
        return self.client.post(self.url, payload, content_type="application/json")

    def test_invalid_request_body_returns_400(self):
        response = self.create_request({})
        self.assertEqual(response.status_code, 400)

    def test_google_auth_verification_error_returns_401(self):
        self.mock_verify_oauth2_token.side_effect = GoogleAuthError(
            "Mocked GoogleAuthError"
        )
        response = self.create_request({"id_token": "token"})
        self.assertEqual(response.status_code, 401)

    def test_google_auth_value_error_returns_401(self):
        self.mock_verify_oauth2_token.side_effect = ValueError("Mocked ValueError")
        response = self.create_request({"id_token": "token"})
        self.assertEqual(response.status_code, 401)

    def test_google_auth_wrong_issuer_returns_401(self):
        self.mock_verify_oauth2_token.return_value = {"iss": "wrong_issuer"}
        response = self.create_request({"id_token": "token"})
        self.assertEqual(response.status_code, 401)

    def test_creates_new_user_if_no_existing_user(self):
        payload = {"id_token": "valid_token"}
        response = self.create_request(payload)
        user_profile = UserProfile.objects.get(user__email="test@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertEqual(user_profile.picture, "http://example.com/picture.jpg")
        self.assertEqual(user_profile.email, "test@example.com")
        self.assertEqual(user_profile.name, "Test User")

    def test_existing_user_sign_in(self):
        payload = {"id_token": "valid_token"}
        response = self.create_request(payload)
        user_profile = UserProfile.objects.get(user__email="test@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertEqual(user_profile.picture, "http://example.com/picture.jpg")
        self.assertEqual(user_profile.name, "Test User")
