import time
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from login.utils import APPLE_ISSUER


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
def mock_google_auth_without_name(settings):
    settings.GOOGLE_CLIENT_ID = "web-client-id"
    settings.GOOGLE_IOS_CLIENT_ID = "ios-client-id"
    with patch("login.utils.google_id_token.verify_oauth2_token") as mock:
        mock.return_value = {
            "iss": "accounts.google.com",
            "aud": "web-client-id",
            "email": "test@example.com",
            "picture": "http://example.com/picture.jpg",
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


@pytest.fixture
def apple_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return private_pem, private_key.public_key()


@pytest.fixture
def patch_apple_key(apple_keypair):
    _, public_key = apple_keypair
    with patch("login.utils._get_apple_public_key", return_value=public_key):
        yield


@pytest.fixture
def apple_id_token_factory(apple_keypair):
    private_pem, _ = apple_keypair

    def make_token(audience):
        now = int(time.time())
        return jwt.encode(
            {
                "iss": APPLE_ISSUER,
                "aud": audience,
                "sub": "001234.apple-user-id.5678",
                "email": "apple@example.com",
                "iat": now,
                "exp": now + 600,
            },
            private_pem,
            algorithm="RS256",
            headers={"kid": "test-kid"},
        )

    return make_token
