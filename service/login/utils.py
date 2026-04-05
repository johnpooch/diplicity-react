import urllib.request
import json

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import exceptions

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"


def _get_valid_client_ids():
    client_ids = []
    if settings.GOOGLE_CLIENT_ID:
        client_ids.append(settings.GOOGLE_CLIENT_ID)
    if settings.GOOGLE_IOS_CLIENT_ID:
        client_ids.append(settings.GOOGLE_IOS_CLIENT_ID)
    return client_ids


def verify_google_id_token(id_token):
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            clock_skew_in_seconds=3,
        )
    except GoogleAuthError:
        raise exceptions.AuthenticationFailed("Google authentication failed")
    except ValueError:
        raise exceptions.AuthenticationFailed("Token verification failed")
    except Exception:
        raise exceptions.AuthenticationFailed("Login failed")

    if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise exceptions.AuthenticationFailed("Wrong issuer")

    valid_client_ids = _get_valid_client_ids()
    if id_info.get("aud") not in valid_client_ids:
        raise exceptions.AuthenticationFailed("Invalid token audience")

    return id_info


def _fetch_apple_public_keys():
    response = urllib.request.urlopen(APPLE_JWKS_URL)
    return json.loads(response.read())


def _decode_base64url_int(val):
    import base64

    padding = 4 - len(val) % 4
    val += "=" * padding
    data = base64.urlsafe_b64decode(val)
    return int.from_bytes(data, byteorder="big")


def _get_apple_public_key(kid):
    jwks = _fetch_apple_public_keys()
    for key_data in jwks["keys"]:
        if key_data["kid"] == kid:
            e = _decode_base64url_int(key_data["e"])
            n = _decode_base64url_int(key_data["n"])
            return RSAPublicNumbers(e, n).public_key(default_backend())
    raise exceptions.AuthenticationFailed("Apple public key not found")


def verify_apple_id_token(id_token):
    try:
        header = jwt.get_unverified_header(id_token)
    except jwt.exceptions.DecodeError:
        raise exceptions.AuthenticationFailed("Invalid Apple identity token")

    public_key = _get_apple_public_key(header["kid"])

    try:
        decoded = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer=APPLE_ISSUER,
        )
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed("Apple token has expired")
    except jwt.InvalidAudienceError:
        raise exceptions.AuthenticationFailed("Invalid token audience")
    except jwt.InvalidIssuerError:
        raise exceptions.AuthenticationFailed("Invalid token issuer")
    except jwt.InvalidTokenError:
        raise exceptions.AuthenticationFailed("Apple authentication failed")

    return decoded
