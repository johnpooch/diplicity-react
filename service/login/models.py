import random
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.conf import settings


class AuthUserManager(models.Manager):
    def create_from_google_id_info(self, id_info):
        email = id_info.get("email")
        name = id_info.get("name")

        user, created = self.get_or_create(
            email=email, defaults={"username": self.generate_username(name), "password": settings.SOCIAL_AUTH_PASSWORD}
        )
        return user, created

    def create_from_apple_id_info(self, decoded_token, first_name=None, last_name=None):
        email = decoded_token.get("email")
        name_parts = [p for p in [first_name, last_name] if p]
        name = " ".join(name_parts) if name_parts else email.split("@")[0]

        user, created = self.get_or_create(
            email=email, defaults={"username": self.generate_username(name), "password": settings.SOCIAL_AUTH_PASSWORD}
        )
        return user, created, name

    def generate_username(self, name):
        username = "".join(name.split(" ")).lower()
        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            return username
        else:
            random_username = username + str(random.randint(0, 1000))
            return self.generate_username(random_username)


class AuthUser(User):
    objects = AuthUserManager()

    class Meta:
        proxy = True
