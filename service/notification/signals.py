import logging
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from channel.models import ChannelMessage
from draw_proposal.models import DrawProposal
from email_service.tasks import send_email_notification
from email_service.templates import notification_email
from game.models import Game
from common.constants import GameStatus, PhaseStatus
from notification.tasks import send_notification
from notification.utils import send_notification_to_users
from phase.models import Phase
from victory.models import Victory

logger = logging.getLogger(__name__)


def _truncate_body(text: str, max_lines: int = 3, max_chars: int = 200) -> str:
    lines = text.split("\n")
    truncated = "\n".join(lines[:max_lines])
    if len(truncated) > max_chars:
        truncated = truncated[:max_chars].rstrip() + "…"
    elif len(lines) > max_lines:
        truncated += "…"
    return truncated


@receiver(post_save, sender=DrawProposal)
def send_draw_proposal_notification(sender, instance, created, **kwargs):
    if not created:
        return

    other_members = instance.game.members.filter(
        eliminated=False, kicked=False, civil_disorder=False
    ).exclude(id=instance.created_by.id)
    user_ids = [member.user_id for member in other_members if member.user_id is not None]
    if instance.game.game_master_id is not None:
        user_ids.append(instance.game.game_master_id)
    if not user_ids:
        return

    game = instance.game
    proposer_name = "Anonymous" if game.anonymity_active else instance.created_by.name
    phase = instance.phase
    link = (
        f"{settings.FRONTEND_URL}/game/{game.id}/phase/{phase.id}/draw-proposals"
        if phase is not None
        else f"{settings.FRONTEND_URL}/game/{game.id}"
    )
    send_notification.defer(
        user_ids=user_ids,
        title=game.name,
        body=f"{proposer_name} has proposed a draw. Respond to it now.",
        notification_type="draw_proposal",
        data={"game_id": str(game.id), "link": link},
    )


_game_status_cache = {}


@receiver(post_save, sender=ChannelMessage)
def send_channel_message_notification(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.channel.private:
        other_members = instance.channel.members.exclude(id=instance.sender.id)
    else:
        other_members = instance.channel.game.members.exclude(id=instance.sender.id)

    user_ids = [member.user_id for member in other_members if member.user_id is not None]
    if not user_ids:
        return

    game = instance.channel.game
    sender_name = "Anonymous" if game.anonymity_active else instance.sender.name
    current_phase = game.phases.last()
    link = (
        f"{settings.FRONTEND_URL}/game/{game.id}/phase/{current_phase.id}/chat/channel/{instance.channel.id}"
        if current_phase
        else f"{settings.FRONTEND_URL}/game/{game.id}"
    )

    send_notification.defer(
        user_ids=user_ids,
        title=game.name,
        body=f"{sender_name}: {_truncate_body(instance.body)}",
        notification_type="channel_message",
        data={
            "game_id": str(game.id),
            "link": link,
        },
    )


@receiver(pre_save, sender=Game)
def cache_game_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Game.objects.get(pk=instance.pk)
            _game_status_cache[instance.pk] = old_instance.status
        except sender.DoesNotExist:
            pass


def _send_game_start_notification(instance):
    user_ids = instance.notification_user_ids()
    if not user_ids:
        return

    link = f"{settings.FRONTEND_URL}/game/{instance.id}"
    body = "The game has started. You can now chat with other players and submit your orders. Good luck!"

    send_notification.defer(
        user_ids=user_ids,
        title=instance.name,
        body=body,
        notification_type="game_start",
        data={"game_id": str(instance.id), "link": link},
    )
    send_email_notification.defer(
        user_ids=user_ids,
        subject=f"{instance.name} — Game Started",
        html=notification_email(
            title=instance.name,
            body=body,
            link=link,
        ),
    )


def _send_game_end_notification(game_id, game_name, all_member_user_ids):
    try:
        victory = Victory.objects.prefetch_related("members").get(game_id=game_id)
    except Victory.DoesNotExist:
        return

    victory_members = list(victory.members.all())
    link = f"{settings.FRONTEND_URL}/game/{game_id}"

    if len(victory_members) >= 2:
        names = ", ".join(m.name for m in victory_members)
        send_notification.defer(
            user_ids=all_member_user_ids,
            title=game_name,
            body=f"The game has ended in a draw, including {names}. Well played!",
            notification_type="game_draw",
            data={"game_id": str(game_id), "link": link},
        )
    elif len(victory_members) == 1:
        winner = victory_members[0]
        winner_user_ids = [winner.user_id] if winner.user_id is not None else []
        other_user_ids = [uid for uid in all_member_user_ids if uid != winner.user_id]
        if winner_user_ids:
            send_notification.defer(
                user_ids=winner_user_ids,
                title=game_name,
                body="The game has ended, you achieved a solo win! Congratulations!",
                notification_type="game_solo_win",
                data={"game_id": str(game_id), "link": link},
            )
        if other_user_ids:
            send_notification.defer(
                user_ids=other_user_ids,
                title=game_name,
                body=f"The game has ended, and {winner.name} achieved a solo win! Better luck next time!",
                notification_type="game_solo_loss",
                data={"game_id": str(game_id), "link": link},
            )


@receiver(post_save, sender=Game)
def send_game_status_notifications(sender, instance, created, **kwargs):
    if created:
        return

    old_status = _game_status_cache.pop(instance.pk, None)

    if old_status == GameStatus.PENDING and instance.status == GameStatus.ACTIVE:
        _send_game_start_notification(instance)
    elif old_status == GameStatus.ACTIVE and instance.status == GameStatus.COMPLETED:
        _send_game_end_notification(instance.id, instance.name, instance.notification_user_ids())


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

        def _send():
            user_ids = instance.game.notification_user_ids()
            link = f"{settings.FRONTEND_URL}/game/{instance.game.id}"
            body = f"{instance.name} has been resolved"

            send_notification_to_users(
                user_ids=user_ids,
                title=instance.game.name,
                body=body,
                notification_type="phase_resolved",
                data={"game_id": str(instance.game.id), "link": link},
            )
            send_email_notification.defer(
                user_ids=user_ids,
                subject=f"{instance.game.name} — {instance.name} Resolved",
                html=notification_email(
                    title=instance.game.name,
                    body=body,
                    link=link,
                ),
            )

        transaction.on_commit(_send)
