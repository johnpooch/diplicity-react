import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from common.constants import PhaseStatus
from member.models import Member
from phase.models import Phase

from bot.constants import BOT_USER_EMAIL
from bot.tasks import play_phase

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Phase)
def trigger_bot_on_active_phase(sender, instance, **kwargs):
    if instance.status != PhaseStatus.ACTIVE:
        return

    game_has_bot = Member.objects.filter(
        game_id=instance.game_id, user__email=BOT_USER_EMAIL
    ).exists()
    if not game_has_bot:
        return

    play_phase.configure(
        lock=f"bot-game-{instance.game_id}",
    ).defer(phase_id=instance.pk)

    logger.info(
        f"Triggered bot turn for phase {instance.pk} (game {instance.game_id})"
    )
