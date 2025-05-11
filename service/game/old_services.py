import json
import os
import random
import requests
from datetime import datetime, timedelta
from django.utils import timezone

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction, models
from django.shortcuts import get_object_or_404
from fcm_django.models import FCMDevice
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Game,
    Variant,
    Order,
    Phase,
    Channel,
    ChannelMessage,
    UserProfile,
    Task,
    Unit,
    SupplyCenter,
)
from . import old_serializers
from .tasks import BaseTask


def auth_generate_username(name):
    username = "".join(name.split(" ")).lower()
    User = get_user_model()
    if not User.objects.filter(username=username).exists():
        return username
    else:
        random_username = username + str(random.randint(0, 1000))
        return auth_generate_username(random_username)


def auth_get_tokens(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def auth_login_or_register(id_token):
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=3,
        )
    except GoogleAuthError as e:
        raise exceptions.AuthenticationFailed(f"Token verification failed: {str(e)}")
    except ValueError:
        raise exceptions.AuthenticationFailed("Token verification failed")

    if id_info["iss"] not in [
        "accounts.google.com",
        "https://accounts.google.com",
    ]:
        raise exceptions.AuthenticationFailed("Wrong issuer")

    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")

    User = get_user_model()
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        # Update UserProfile for existing user
        profile = UserProfile.objects.filter(user=existing_user).first()
        if not profile:
            UserProfile.objects.create(user=existing_user, name=name, picture=picture)
        else:
            profile.name = name
            profile.picture = picture
            profile.save()
        return existing_user
    else:
        user = {
            "email": email,
            "username": auth_generate_username(name),
            "password": os.environ.get("SOCIAL_SECRET"),
        }
        user = User.objects.create_user(**user)
        user.is_verified = True
        user.save()

        # Create UserProfile for new user
        UserProfile.objects.create(user=user, name=name, picture=picture)
        return user
