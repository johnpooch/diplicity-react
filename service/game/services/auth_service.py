import os
import random
import logging
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import exceptions
from .. import models

logger = logging.getLogger("game")


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
        logger.info(f"AuthService.login_or_register called")
        try:
            id_info = google_id_token.verify_oauth2_token(
                id_token,
                google_requests.Request(),
                os.environ.get("GOOGLE_CLIENT_ID"),
                clock_skew_in_seconds=3,
            )
            logger.info("ID infor retrieved from Google")
        except GoogleAuthError:
            logger.error("Login failed: Google authentication failed")
            raise exceptions.AuthenticationFailed("Google authentication failed")
        except ValueError:
            logger.error("Login failed: Token verification failed")
            raise exceptions.AuthenticationFailed("Token verification failed")
        except Exception as e:
            logger.error(f"Login failed with unexpected error: {e}")
            raise exceptions.AuthenticationFailed("Login failed")

        if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            logger.error("Login failed: Wrong issuer")
            raise exceptions.AuthenticationFailed("Wrong issuer")

        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")

        User = get_user_model()
        user = User.objects.filter(email=email).first()

        if user:
            logger.info("User already exists")
            profile, created = models.UserProfile.objects.get_or_create(user=user)
            if created:
                logger.info("User profile created")
            else:
                logger.info("User profile already exists")
            profile.name = name
            profile.picture = picture
            profile.save()
        else:
            logger.info("User does not exist, creating user")
            user = User.objects.create_user(
                email=email,
                username=self.generate_username(name),
                password=os.environ.get("SOCIAL_SECRET"),
            )
            user.is_verified = True
            user.save()
            logger.info("User created")
            profile = models.UserProfile.objects.create(user=user, name=name, picture=picture)
            logger.info("User profile created")

        logger.info("Getting tokens")
        tokens = self.get_tokens(user)
        logger.info("Tokens retrieved")

        return user, tokens
