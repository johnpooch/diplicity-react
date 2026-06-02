import time
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from rest_framework.exceptions import AuthenticationFailed

from login.utils import APPLE_ISSUER, verify_apple_id_token


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


def _make_token(private_pem, audience):
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


@pytest.fixture
def patch_apple_key(apple_keypair):
    _, public_key = apple_keypair
    with patch("login.utils._get_apple_public_key", return_value=public_key):
        yield


@pytest.mark.parametrize("audience", ["com.diplicity.app", "com.diplicity.web"])
def test_accepts_native_and_web_audiences(
    settings, apple_keypair, patch_apple_key, audience
):
    settings.APPLE_CLIENT_ID = "com.diplicity.app"
    settings.APPLE_WEB_CLIENT_ID = "com.diplicity.web"
    private_pem, _ = apple_keypair

    decoded = verify_apple_id_token(_make_token(private_pem, audience))

    assert decoded["aud"] == audience
    assert decoded["email"] == "apple@example.com"


def test_rejects_unknown_audience(settings, apple_keypair, patch_apple_key):
    settings.APPLE_CLIENT_ID = "com.diplicity.app"
    settings.APPLE_WEB_CLIENT_ID = "com.diplicity.web"
    private_pem, _ = apple_keypair

    with pytest.raises(AuthenticationFailed):
        verify_apple_id_token(_make_token(private_pem, "com.someone.else"))


def test_web_audience_absent_when_unset(settings, apple_keypair, patch_apple_key):
    settings.APPLE_CLIENT_ID = "com.diplicity.app"
    settings.APPLE_WEB_CLIENT_ID = None
    private_pem, _ = apple_keypair

    with pytest.raises(AuthenticationFailed):
        verify_apple_id_token(_make_token(private_pem, "com.diplicity.web"))
