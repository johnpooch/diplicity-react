import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from phase.models import Phase, PhaseState

from bot.decorators import (
    capture_phase_status,
    on_orders_confirmed,
    on_phase_activated,
    when_humans_confirmed,
    with_bot_members,
)
from bot.tasks import finalize as finalize_task
from bot.tasks import plan as plan_task

logger = logging.getLogger(__name__)


pre_save.connect(capture_phase_status, sender=Phase)


@receiver(post_save, sender=Phase)
@on_phase_activated
@with_bot_members
def plan(sender, instance, bot_members, **kwargs):
    logger.info(f"[bot.plan signal] phase {instance.id} activated for game {instance.game_id}")
    for member in bot_members:
        plan_task.configure(lock=f"plan-{instance.id}-{member.id}").defer(
            user_id=member.user_id, game_id=instance.game_id
        )
        logger.info(
            f"[bot.plan signal] queued plan for member {member.id} (phase {instance.id})"
        )


@receiver(post_save, sender=PhaseState)
@on_orders_confirmed
@when_humans_confirmed
def finalize(sender, instance, phase, bot_phase_states, **kwargs):
    logger.info(
        f"[bot.finalize signal] all humans confirmed for phase {phase.id} (game {phase.game_id})"
    )
    for phase_state in bot_phase_states:
        finalize_task.configure(
            lock=f"finalize-{phase.id}-{phase_state.member_id}"
        ).defer(user_id=phase_state.member.user_id, game_id=phase.game_id)
        logger.info(
            f"[bot.finalize signal] queued finalize for member {phase_state.member_id} "
            f"(phase {phase.id})"
        )
