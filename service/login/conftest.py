import pytest
from unittest.mock import patch


@pytest.fixture
def mock_google_auth():
    with patch("login.utils.google_id_token.verify_oauth2_token") as mock:
        mock.return_value = {
            "iss": "accounts.google.com",
            "email": "test@example.com",
            "name": "Test User",
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