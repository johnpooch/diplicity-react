import random
from django.db import IntegrityError, models, transaction
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


class AuthUserManager(models.Manager):
    def create_from_google_id_info(self, id_info):
        email = id_info.get("email")
        name = id_info.get("name") or email.split("@")[0]

        user, created = self._get_or_create_social_user(email, name)
        return user, created, name

    def create_from_apple_id_info(self, decoded_token, first_name=None, last_name=None):
        email = decoded_token.get("email")
        name_parts = [p for p in [first_name, last_name] if p]
        name = " ".join(name_parts) if name_parts else email.split("@")[0]

        user, created = self._get_or_create_social_user(email, name)
        return user, created, name

    def _get_or_create_social_user(self, email, name):
        user = self.filter(email__iexact=email).first()
        if user is None:
            try:
                return self._create_social_user(email, name), True
            except IntegrityError:
                user = self.filter(email__iexact=email).first()
                if user is None:
                    raise
        if not user.is_active:
            user.set_unusable_password()
            user.is_active = True
            user.save(update_fields=["password", "is_active"])
        return user, False

    def _create_social_user(self, email, name):
        user = self.model(username=self.generate_username(name), email=email)
        user.set_unusable_password()
        with transaction.atomic():
            user.save()
        return user

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
