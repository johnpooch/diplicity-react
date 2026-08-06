from bot_profile.constants import BotKind
from bot_profile.models import BotProfile
from common.constants import PhaseStatus

from agent.constants import AgentTaskKind

REGISTRY = {}


def register(event_type):
    def decorator(cls):
        cls.event_type = event_type
        REGISTRY[event_type] = cls
        return cls

    return decorator


def get_spec(event_type, context):
    spec_class = REGISTRY.get(event_type)
    if spec_class is None:
        return None
    return spec_class(context)


def _finalize_tasks(phase):
    bot_phase_states = phase.phase_states.filter(
        has_possible_orders=True,
        orders_confirmed=False,
        member__user__bot_profile__isnull=False,
    ).select_related("member")
    return [
        {"kind": AgentTaskKind.FINALIZE, "member": phase_state.member, "phase": phase}
        for phase_state in bot_phase_states
    ]


class AgentTaskSpec:
    event_type = None

    def __init__(self, context):
        self.context = context

    def get_tasks(self):
        raise NotImplementedError


@register("phase_started")
class PhaseStartedSpec(AgentTaskSpec):
    def get_tasks(self):
        phase = self.context.phase
        plan = [{"kind": AgentTaskKind.PLAN, "member": member, "phase": phase} for member in phase.game.bot_members]
        if not plan:
            return []
        if phase.has_unconfirmed_human:
            return plan

        finalize = _finalize_tasks(phase)
        finalizing = {task["member"].id for task in finalize}
        return finalize + [task for task in plan if task["member"].id not in finalizing]


@register("phase_state_confirmed")
class PhaseStateConfirmedSpec(AgentTaskSpec):
    def get_tasks(self):
        phase = self.context.phase
        if phase.status != PhaseStatus.ACTIVE:
            return []
        if phase.has_unconfirmed_human:
            return []
        return _finalize_tasks(phase)


@register("channel_message")
class ChannelMessageSpec(AgentTaskSpec):
    def get_tasks(self):
        actor = self.context.actor
        if actor is None or BotProfile.objects.filter(user=actor).exists():
            return []
        bot_members = self.context.channel.members.filter(user__bot_profile__kind=BotKind.LLM).select_related("user")
        return [
            {
                "kind": AgentTaskKind.REPLY,
                "member": member,
                "phase": self.context.phase,
                "message": self.context.message,
            }
            for member in bot_members
        ]
