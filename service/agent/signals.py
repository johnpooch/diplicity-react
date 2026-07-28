from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from channel.models import ChannelMessage
from phase.models import Phase, PhaseState

from agent.constants import AgentTaskKind
from agent.decorators import (
    capture_phase_status,
    on_human_chat_message,
    on_orders_confirmed,
    on_phase_activated,
    when_humans_confirmed,
    with_bot_channel_members,
    with_bot_members,
)
from agent.models import AgentTask

pre_save.connect(capture_phase_status, sender=Phase)


@receiver(post_save, sender=Phase)
@on_phase_activated
@with_bot_members
def plan(sender, instance, bot_members, **kwargs):
    for member in bot_members:
        AgentTask.objects.create_from_event(kind=AgentTaskKind.PLAN, member=member, phase=instance)


@receiver(post_save, sender=PhaseState)
@on_orders_confirmed
@when_humans_confirmed
def finalize(sender, instance, phase, bot_phase_states, **kwargs):
    for phase_state in bot_phase_states:
        AgentTask.objects.create_from_event(kind=AgentTaskKind.FINALIZE, member=phase_state.member, phase=phase)


@receiver(post_save, sender=ChannelMessage)
@on_human_chat_message
@with_bot_channel_members
def reply(sender, instance, bot_members, **kwargs):
    for member in bot_members:
        AgentTask.objects.create_from_event(
            kind=AgentTaskKind.REPLY, member=member, phase=instance.phase, message=instance
        )
