from django.db import transaction

from agent.constants import AgentTaskKind
from agent.models import AgentTask
from common.constants import PhaseStatus
from order.models import Order


class ReplanError(Exception):
    pass


def replan(member):
    if member.user is None or not hasattr(member.user, "bot_profile"):
        raise ReplanError(f"{member} is not played by a bot")
    if member.kicked:
        raise ReplanError(f"{member} has been kicked")

    phase = member.game.current_phase
    if phase is None or phase.status != PhaseStatus.ACTIVE:
        raise ReplanError(f"game '{member.game_id}' has no active phase")

    with transaction.atomic():
        Order.objects.filter(phase_state__member=member, phase_state__phase=phase).delete()
        return AgentTask.objects.requeue(kind=AgentTaskKind.PLAN, member=member, phase=phase)
