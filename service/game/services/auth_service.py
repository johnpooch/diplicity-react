import os
import random
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import exceptions
from .. import models


class AuthService:
    def generate_username(self, name):
        username = "".join(name.split(" ")).lower()
        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            return username
        else:
            random_username = username + str(random.randint(0, 1000))
            return self.generate_username(random_username)

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

    def login_or_register(self, id_token):
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

        if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise exceptions.AuthenticationFailed("Wrong issuer")

        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")

        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user:
            profile, _ = models.UserProfile.objects.get_or_create(user=user)
            profile.name = name
            profile.picture = picture
            profile.save()
        else:
            user = User.objects.create_user(
                email=email,
                username=self.generate_username(name),
                password=os.environ.get("SOCIAL_SECRET"),
            )
            user.is_verified = True
            user.save()
            models.UserProfile.objects.create(user=user, name=name, picture=picture)

        tokens = self.get_tokens(user)
        return user, tokens
