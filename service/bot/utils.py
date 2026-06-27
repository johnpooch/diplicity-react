from django.conf import settings
from django.contrib.auth import get_user_model

from common.constants import OrderType

from bot.constants import BOT_USER_EMAIL


def get_bot_user():
    User = get_user_model()
    return User.objects.get(email=BOT_USER_EMAIL)


def user_can_use_bot_opponent(user):
    if user is None or not user.email:
        return False
    return user.email.lower() in settings.BOT_OPPONENT_ALLOWLIST


def bot_request_host():
    for host in settings.ALLOWED_HOSTS:
        if host and host != "*":
            return host.lstrip(".")
    return "testserver"


def option_to_selected(option):
    order_type = option["order_type"]["id"]
    selected = [option["source"]["id"], order_type]

    if order_type == OrderType.BUILD:
        selected.append(option["unit_type"]["id"])
        if option["named_coast"]:
            selected.append(option["named_coast"]["id"])
    elif order_type in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY):
        selected.append(option["target"]["id"])
        if option["named_coast"]:
            selected.append(option["named_coast"]["id"])
    elif order_type in (OrderType.SUPPORT, OrderType.CONVOY):
        selected.append(option["aux"]["id"])
        selected.append(option["target"]["id"])

    return selected


def first_legal_selections(options):
    first_by_source = {}
    for option in options:
        source_id = option["source"]["id"]
        if source_id not in first_by_source:
            first_by_source[source_id] = option_to_selected(option)
    return list(first_by_source.values())
