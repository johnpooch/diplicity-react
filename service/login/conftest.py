import pytest
from unittest.mock import patch


@pytest.fixture
def mock_google_auth(settings):
    settings.GOOGLE_CLIENT_ID = "web-client-id"
    settings.GOOGLE_IOS_CLIENT_ID = "ios-client-id"
    with patch("login.utils.google_id_token.verify_oauth2_token") as mock:
        mock.return_value = {
            "iss": "accounts.google.com",
            "aud": "web-client-id",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/picture.jpg",
        }
        yield mock


@pytest.fixture
def mock_google_auth_without_picture(settings):
    settings.GOOGLE_CLIENT_ID = "web-client-id"
    settings.GOOGLE_IOS_CLIENT_ID = "ios-client-id"
    with patch("login.utils.google_id_token.verify_oauth2_token") as mock:
        mock.return_value = {
            "iss": "accounts.google.com",
            "aud": "web-client-id",
            "email": "test@example.com",
            "name": "Test User",
        }
        yield mock


@pytest.fixture
def mock_refresh_token():
    with patch("login.serializers.RefreshToken.for_user") as mock:
        mock.return_value = type(
            "MockRefreshToken",
            (object,),
            {
                "access_token": "access_token",
                "__str__": lambda self: "refresh_token",
            },
        )()
        yield mock


@pytest.fixture
def mock_send_email():
    with patch("login.serializers.send_email") as mock:
        yield mock


@pytest.fixture
def mock_apple_auth(settings):
    settings.APPLE_CLIENT_ID = "com.diplicity.app"
    with patch("login.serializers.verify_apple_id_token") as mock:
        mock.return_value = {
            "iss": "https://appleid.apple.com",
            "aud": "com.diplicity.app",
            "sub": "001234.apple-user-id.5678",
            "email": "apple@example.com",
        }
        yield mock


@pytest.fixture
def mock_apple_auth_relay_email(settings):
    settings.APPLE_CLIENT_ID = "com.diplicity.app"
    with patch("login.serializers.verify_apple_id_token") as mock:
        mock.return_value = {
            "iss": "https://appleid.apple.com",
            "aud": "com.diplicity.app",
            "sub": "001234.apple-user-id.5678",
            "email": "abc123@privaterelay.appleid.com",
        }
        yield mock
