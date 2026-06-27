from django.conf import settings
from django.contrib.auth import get_user_model

from bot.constants import BOT_USER_EMAIL


def get_bot_user():
    User = get_user_model()
    return User.objects.get(email=BOT_USER_EMAIL)


def user_can_use_bot_opponent(user):
    if user is None or not user.email:
        return False
    return user.email.lower() in settings.BOT_OPPONENT_ALLOWLIST
