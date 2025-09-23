import os
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import exceptions


def verify_google_id_token(id_token):
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            os.environ.get("GOOGLE_CLIENT_ID"),
            clock_skew_in_seconds=3,
        )
    except GoogleAuthError:
        raise exceptions.AuthenticationFailed("Google authentication failed")
    except ValueError:
        raise exceptions.AuthenticationFailed("Token verification failed")
    except Exception as e:
        raise exceptions.AuthenticationFailed("Login failed")

    if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise exceptions.AuthenticationFailed("Wrong issuer")

    return id_info