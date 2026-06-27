import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from common.constants import PhaseStatus
from member.models import Member
from phase.models import Phase, PhaseState

from bot.constants import BOT_USER_EMAIL
from bot.decorators import capture_phase_status, on_phase_activated, with_bot_members
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
def finalize(sender, instance, **kwargs):
    if not instance.orders_confirmed:
        return

    bot_user_ids = set(
        Member.objects.filter(
            game__phases=instance.phase_id, user__email=BOT_USER_EMAIL
        ).values_list("user_id", flat=True)
    )
    if not bot_user_ids:
        return

    phase = instance.phase
    if phase.status != PhaseStatus.ACTIVE:
        return

    human_states = phase.phase_states.filter(has_possible_orders=True).exclude(
        member__user_id__in=bot_user_ids
    )
    if human_states.filter(orders_confirmed=False).exists():
        return

    bot_states = phase.phase_states.filter(
        has_possible_orders=True,
        orders_confirmed=False,
        member__user_id__in=bot_user_ids,
    ).select_related("member")

    logger.info(
        f"[bot.finalize signal] all humans confirmed for phase {phase.id} "
        f"(game {phase.game_id})"
    )
    for phase_state in bot_states:
        finalize_task.configure(
            lock=f"finalize-{phase.id}-{phase_state.member_id}"
        ).defer(user_id=phase_state.member.user_id, game_id=phase.game_id)
        logger.info(
            f"[bot.finalize signal] queued finalize for member {phase_state.member_id} "
            f"(phase {phase.id})"
        )
