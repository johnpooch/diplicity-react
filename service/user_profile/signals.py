import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from user_profile.models import UserProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserProfile)
def create_welcome_sandbox_game(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user

    try:
        from game.models import Game
        from variant.models import Variant

        if Game.objects.filter(sandbox=True, members__user=user).exists():
            return

        variant = Variant.objects.with_game_creation_data().filter(id="classical").first()
        if variant is None:
            logger.warning("Classical variant not found — skipping welcome game for user %s", user.id)
            return

        Game.objects.create_sandbox(
            user=user,
            name="Practice Game",
            variant=variant,
        )
    except Exception:
        logger.warning("Failed to create welcome sandbox game for user %s", user.id, exc_info=True)
