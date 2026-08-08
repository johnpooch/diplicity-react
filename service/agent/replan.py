from django.db import transaction

from agent.constants import AgentTaskKind
from agent.models import AgentTask
from order.models import Order
from phase.models import Phase


class ReplanError(Exception):
    pass


def replan(member):
    if member.user is None or not hasattr(member.user, "bot_profile"):
        raise ReplanError(f"{member} is not played by a bot")
    if member.kicked:
        raise ReplanError(f"{member} has been kicked")

    phase = member.game.current_phase

    with transaction.atomic():
        if phase is None or Phase.objects.lock_if_active(phase.id) is None:
            raise ReplanError(f"game '{member.game_id}' has no active phase")
        Order.objects.filter(phase_state__member=member, phase_state__phase=phase).delete()
        return AgentTask.objects.requeue(kind=AgentTaskKind.PLAN, member=member, phase=phase)
