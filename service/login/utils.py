from django.conf import settings
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import exceptions


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
