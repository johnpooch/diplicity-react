from bot_profile.models import BotProfile
from common.constants import PhaseStatus
from member.models import Member

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


def _bot_user_ids_for_phase(phase_id):
    return set(
        Member.objects.filter(game__phases=phase_id, user__bot_profile__isnull=False).values_list("user_id", flat=True)
    )


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
        bot_members = Member.objects.filter(game_id=phase.game_id, user__bot_profile__isnull=False).select_related(
            "user"
        )
        return [{"kind": AgentTaskKind.PLAN, "member": member, "phase": phase} for member in bot_members]


@register("phase_state_confirmed")
class PhaseStateConfirmedSpec(AgentTaskSpec):
    def get_tasks(self):
        phase = self.context.phase
        bot_user_ids = _bot_user_ids_for_phase(phase.id)
        if not bot_user_ids:
            return []
        if phase.status != PhaseStatus.ACTIVE:
            return []

        humans_pending = (
            phase.phase_states.filter(has_possible_orders=True, orders_confirmed=False)
            .exclude(member__user_id__in=bot_user_ids)
            .exists()
        )
        if humans_pending:
            return []

        bot_phase_states = phase.phase_states.filter(
            has_possible_orders=True,
            orders_confirmed=False,
            member__user_id__in=bot_user_ids,
        ).select_related("member")
        return [
            {"kind": AgentTaskKind.FINALIZE, "member": phase_state.member, "phase": phase}
            for phase_state in bot_phase_states
        ]


@register("channel_message")
class ChannelMessageSpec(AgentTaskSpec):
    def get_tasks(self):
        actor = self.context.actor
        if actor is None or BotProfile.objects.filter(user=actor).exists():
            return []
        bot_members = self.context.channel.members.filter(user__bot_profile__isnull=False).select_related("user")
        return [
            {
                "kind": AgentTaskKind.REPLY,
                "member": member,
                "phase": self.context.phase,
                "message": self.context.message,
            }
            for member in bot_members
        ]
