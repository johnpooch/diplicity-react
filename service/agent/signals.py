import logging

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
from agent.tasks import run as run_task

logger = logging.getLogger(__name__)


pre_save.connect(capture_phase_status, sender=Phase)


@receiver(post_save, sender=Phase)
@on_phase_activated
@with_bot_members
def plan(sender, instance, bot_members, **kwargs):
    logger.info(f"[agent.plan signal] phase {instance.id} activated for game {instance.game_id}")
    for member in bot_members:
        task, _ = AgentTask.objects.enqueue(kind=AgentTaskKind.PLAN, member=member, phase=instance)
        run_task.configure(lock=f"agent-task-{task.id}").defer(agent_task_id=task.id)
        logger.info(f"[agent.plan signal] queued plan task {task.id} for member {member.id} (phase {instance.id})")


@receiver(post_save, sender=PhaseState)
@on_orders_confirmed
@when_humans_confirmed
def finalize(sender, instance, phase, bot_phase_states, **kwargs):
    logger.info(f"[agent.finalize signal] all humans confirmed for phase {phase.id} (game {phase.game_id})")
    for phase_state in bot_phase_states:
        task, _ = AgentTask.objects.enqueue(kind=AgentTaskKind.FINALIZE, member=phase_state.member, phase=phase)
        run_task.configure(lock=f"agent-task-{task.id}").defer(agent_task_id=task.id)
        logger.info(
            f"[agent.finalize signal] queued finalize task {task.id} for member {phase_state.member_id} "
            f"(phase {phase.id})"
        )


@receiver(post_save, sender=ChannelMessage)
@on_human_chat_message
@with_bot_channel_members
def reply(sender, instance, bot_members, **kwargs):
    logger.info(
        f"[agent.reply signal] message {instance.id} in channel {instance.channel_id} "
        f"(game {instance.channel.game_id})"
    )
    for member in bot_members:
        task, _ = AgentTask.objects.enqueue(
            kind=AgentTaskKind.REPLY,
            member=member,
            phase=instance.phase,
            channel=instance.channel,
            message=instance,
        )
        run_task.configure(lock=f"agent-task-{task.id}").defer(agent_task_id=task.id)
        logger.info(f"[agent.reply signal] queued reply task {task.id} for member {member.id} (message {instance.id})")
