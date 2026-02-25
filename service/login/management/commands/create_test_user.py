import json

from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import RefreshToken

from login.models import AuthUser
from user_profile.models import UserProfile


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, required=True)
        parser.add_argument("--name", type=str, required=True)

    def handle(self, *args, **options):
        email = options["email"]
        name = options["name"]

        user, _ = AuthUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "password": "unused",
            },
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={"name": name},
        )

        refresh = RefreshToken.for_user(user)
        self.stdout.write(
            json.dumps(
                {
                    "accessToken": str(refresh.access_token),
                    "refreshToken": str(refresh),
                    "email": email,
                    "name": name,
                }
            )
        )
