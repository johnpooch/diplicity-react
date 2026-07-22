import json

from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import RefreshToken

from login.models import AuthUser
from user_profile.models import UserProfile


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, default="test@example.com")
        parser.add_argument("--name", type=str, default="Test User")
        parser.add_argument("--password", type=str, default="password")
        parser.add_argument("--superuser", action="store_true")

    def handle(self, *args, **options):
        email = options["email"]
        name = options["name"]
        password = options.get("password")
        superuser = options["superuser"]

        user, created = AuthUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "is_active": True,
            },
        )

        user.is_active = True
        user.is_staff = superuser
        user.is_superuser = superuser
        if password:
            user.set_password(password)
        user.save()

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
                    "password": password,
                    "superuser": superuser,
                }
            )
        )
