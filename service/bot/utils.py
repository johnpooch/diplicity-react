from django.conf import settings
from django.contrib.auth import get_user_model


def get_bot_user():
    User = get_user_model()
    return User.objects.get(bot_profile__isnull=False)


def user_can_use_bot_opponent(user):
    if user is None or not user.email:
        return False
    return user.email.lower() in settings.BOT_OPPONENT_ALLOWLIST


def bot_request_host():
    for host in settings.ALLOWED_HOSTS:
        if host and host != "*":
            return host.lstrip(".")
    return "testserver"
