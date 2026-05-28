import logging
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from channel.models import ChannelMessage
from game.models import Game
from common.constants import GameStatus, PhaseStatus
from notification.utils import send_notification_to_users
from phase.models import Phase

logger = logging.getLogger(__name__)


def _truncate_body(text: str, max_lines: int = 3, max_chars: int = 200) -> str:
    lines = text.split("\n")
    truncated = "\n".join(lines[:max_lines])
    if len(truncated) > max_chars:
        truncated = truncated[:max_chars].rstrip() + "…"
    elif len(lines) > max_lines:
        truncated += "…"
    return truncated


_game_status_cache = {}


@receiver(post_save, sender=ChannelMessage)
def send_channel_message_notification(sender, instance, created, **kwargs):
    if not created:
        return

    def send_notification():
        if instance.channel.private:
            other_members = instance.channel.members.exclude(id=instance.sender.id)
        else:
            other_members = instance.channel.game.members.exclude(id=instance.sender.id)

        user_ids = [member.user_id for member in other_members if member.user_id is not None]

        sender_name = instance.sender.name
        game = instance.channel.game
        current_phase = game.phases.last()
        link = (
            f"https://diplicity.com/game/{game.id}/phase/{current_phase.id}/chat/channel/{instance.channel.id}"
            if current_phase
            else f"https://diplicity.com/game/{game.id}"
        )
        send_notification_to_users(
            user_ids=user_ids,
            title=game.name,
            body=f"{sender_name}: {_truncate_body(instance.body)}",
            notification_type="channel_message",
            data={
                "game_id": str(game.id),
                "link": link,
            },
        )

    transaction.on_commit(send_notification)


@receiver(pre_save, sender=Game)
def cache_game_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Game.objects.get(pk=instance.pk)
            _game_status_cache[instance.pk] = old_instance.status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=Game)
def send_game_start_notification(sender, instance, created, **kwargs):
    if created:
        return

    old_status = _game_status_cache.pop(instance.pk, None)
    if old_status == GameStatus.PENDING and instance.status == GameStatus.ACTIVE:

        def send_notification():
            user_ids = [member.user_id for member in instance.members.all() if member.user_id is not None]

            send_notification_to_users(
                user_ids=user_ids,
                title="Game Started",
                body=f"Game '{instance.name}' has started!",
                notification_type="game_start",
                data={
                    "game_id": str(instance.id),
                    "link": f"https://diplicity.com/game/{instance.id}",
                },
            )

        transaction.on_commit(send_notification)


_phase_status_cache = {}


@receiver(pre_save, sender=Phase)
def cache_phase_status(sender, instance, **kwargs):  # noqa: ARG001
    if instance.pk:
        try:
            old_instance = Phase.objects.get(pk=instance.pk)
            _phase_status_cache[instance.pk] = old_instance.status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=Phase)
def send_phase_resolved_notification(sender, instance, created, **kwargs):  # noqa: ARG001
    if created:
        return

    old_status = _phase_status_cache.pop(instance.pk, None)
    if old_status == PhaseStatus.ACTIVE and instance.status == PhaseStatus.COMPLETED:

        def send_notification():
            user_ids = [member.user_id for member in instance.game.members.all() if member.user_id is not None]

            send_notification_to_users(
                user_ids=user_ids,
                title="Phase Resolved",
                body=f"Phase '{instance.name}' has been resolved!",
                notification_type="phase_resolved",
                data={
                    "game_id": str(instance.game.id),
                    "link": f"https://diplicity.com/game/{instance.game.id}",
                },
            )

        transaction.on_commit(send_notification)
