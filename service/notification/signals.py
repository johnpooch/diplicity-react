import logging
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from channel.models import ChannelMessage
from draw_proposal.models import DrawProposal
from email_service.tasks import send_email_notification
from email_service.templates import notification_email
from game.models import Game
from member.models import Member
from common.constants import DeadlineMode, GameStatus
from notification.decorators import capture_phase_status, on_phase_resolved
from notification.events import (
    game_deadline_extended,
    game_deleted_by_master,
    member_kicked_from_staging,
    member_removed_from_staging,
    nmr_extensions_applied,
)
from notification.tasks import send_notification
from notification.utils import send_notification_to_users
from phase.models import Phase
from phase.utils import format_deadline
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
_previous_game_management_state = {}


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
            _previous_game_management_state[instance.pk] = {
                "admin_id": old_instance.admin_id,
                "paused_at": old_instance.paused_at,
            }
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


pre_save.connect(capture_phase_status, sender=Phase)


@receiver(post_save, sender=Phase)
@on_phase_resolved
def send_phase_resolved_notification(sender, instance, created, **kwargs):
    resolved_early = (
        instance.game.deadline_mode == DeadlineMode.FIXED_TIME
        and instance.scheduled_resolution is not None
        and timezone.now() < instance.scheduled_resolution
    )

    def _send():
        user_ids = instance.game.notification_user_ids()
        link = f"{settings.FRONTEND_URL}/game/{instance.game.id}"
        if resolved_early:
            body = f"{instance.name} resolved early — all players confirmed their orders."
            notification_type = "phase_resolved_early"
            subject = f"{instance.game.name} — {instance.name} Resolved Early"
        else:
            body = f"{instance.name} has been resolved"
            notification_type = "phase_resolved"
            subject = f"{instance.game.name} — {instance.name} Resolved"

        send_notification_to_users(
            user_ids=user_ids,
            title=instance.game.name,
            body=body,
            notification_type=notification_type,
            data={"game_id": str(instance.game.id), "link": link},
        )
        send_email_notification.defer(
            user_ids=user_ids,
            subject=subject,
            html=notification_email(
                title=instance.game.name,
                body=body,
                link=link,
            ),
        )

    transaction.on_commit(_send)


def _game_manager_suffix(game):
    return "" if game.anonymity_active else f" ({game.admin.username})"


def _notify_admin_reassigned(game):
    if game.admin_id is None:
        return
    send_notification.defer(
        user_ids=[game.admin_id],
        title=game.name,
        body="The previous manager is no longer available, so you are now managing this game.",
        notification_type="game_admin_reassigned",
        data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
    )


def _notify_game_paused(game):
    user_ids = game.notification_user_ids(exclude_user_id=game.admin_id)
    if not user_ids:
        return
    body = f"Game paused by {game.manager_label}{_game_manager_suffix(game)}"

    def _send():
        send_notification_to_users(
            user_ids=user_ids,
            title=game.name,
            body=body,
            notification_type="game_paused",
            data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
        )

    transaction.on_commit(_send)


def _notify_game_resumed(game):
    user_ids = game.notification_user_ids(exclude_user_id=game.admin_id)
    if not user_ids:
        return
    new_deadline = game.current_phase.scheduled_resolution if game.current_phase else None
    deadline_str = format_deadline(new_deadline, game.fixed_deadline_timezone) if new_deadline else "N/A"
    body = f"Game resumed by {game.manager_label}{_game_manager_suffix(game)}. New deadline: {deadline_str}"

    def _send():
        send_notification_to_users(
            user_ids=user_ids,
            title=game.name,
            body=body,
            notification_type="game_resumed",
            data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
        )

    transaction.on_commit(_send)


@receiver(post_save, sender=Game)
def send_game_management_notifications(sender, instance, created, **kwargs):
    previous_state = _previous_game_management_state.pop(instance.pk, None)
    if created or previous_state is None:
        return

    if previous_state["admin_id"] != instance.admin_id:
        _notify_admin_reassigned(instance)

    if previous_state["paused_at"] is None and instance.paused_at is not None:
        _notify_game_paused(instance)
    elif previous_state["paused_at"] is not None and instance.paused_at is None:
        _notify_game_resumed(instance)


_previous_member_state = {}


@receiver(pre_save, sender=Member)
def capture_member_state(sender, instance, **kwargs):
    if instance.pk:
        _previous_member_state[instance.pk] = (
            Member.objects.filter(pk=instance.pk).values("eliminated", "civil_disorder").first()
        )


def _notify_elimination(member):
    if member.user_id is None:
        return
    game = member.game
    send_notification.defer(
        user_ids=[member.user_id],
        title=game.name,
        body="You've been eliminated. You are not required to enter any orders anymore. You can still chat with players. Better luck next time!",
        notification_type="elimination",
        data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
    )


def _notify_civil_disorder_recovery(member):
    game = member.game
    user_ids = game.notification_user_ids(exclude_user_id=member.user_id)
    if not user_ids:
        return
    nation_name = member.nation.name if member.nation else "A player"

    def _send():
        send_notification_to_users(
            user_ids=user_ids,
            title="Player Returned",
            body=f"{nation_name} has returned from civil disorder.",
            notification_type="civil_disorder_recovery",
            data={"game_id": str(game.id)},
        )

    transaction.on_commit(_send)


@receiver(post_save, sender=Member)
def send_member_notifications(sender, instance, created, **kwargs):
    previous_state = _previous_member_state.pop(instance.pk, None)
    if created or previous_state is None:
        return

    if not previous_state["eliminated"] and instance.eliminated:
        _notify_elimination(instance)

    if previous_state["civil_disorder"] and not instance.civil_disorder:
        _notify_civil_disorder_recovery(instance)


@receiver(game_deleted_by_master)
def send_game_deleted_notification(sender, game, actor_id, **kwargs):
    user_ids = game.notification_user_ids(exclude_user_id=actor_id)
    if not user_ids:
        return
    game_name = game.name

    def _send():
        send_notification.defer(
            user_ids=user_ids,
            title=game_name,
            body="The game was deleted by the Game Master.",
            notification_type="game_deleted",
        )

    transaction.on_commit(_send)


@receiver(game_deadline_extended)
def send_game_deadline_extended_notification(sender, game, **kwargs):
    user_ids = game.notification_user_ids(exclude_user_id=game.admin_id)
    if not user_ids:
        return
    new_deadline = game.current_phase.scheduled_resolution if game.current_phase else None
    deadline_str = format_deadline(new_deadline, game.fixed_deadline_timezone) if new_deadline else "N/A"
    body = f"Deadline extended by {game.manager_label}{_game_manager_suffix(game)}. New deadline: {deadline_str}"

    def _send():
        send_notification_to_users(
            user_ids=user_ids,
            title=game.name,
            body=body,
            notification_type="game_deadline_extended",
            data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
        )

    transaction.on_commit(_send)


@receiver(member_kicked_from_staging)
def send_kicked_from_staging_notification(sender, game, user_id, **kwargs):
    send_notification.defer(
        user_ids=[user_id],
        title=game.name,
        body=f"You were removed from this game by {game.manager_label}.",
        notification_type="kicked_from_staging",
        data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
    )


@receiver(member_removed_from_staging)
def send_removed_from_staging_notification(sender, user_id, game, **kwargs):
    send_notification.defer(
        user_ids=[user_id],
        title="Removed from staging games",
        body=f"You were removed from {game.name} because you entered civil disorder in an active game.",
        notification_type="removed_from_staging",
    )


@receiver(nmr_extensions_applied)
def send_nmr_extension_notifications(sender, phase, extension_members, deadline_str, **kwargs):
    game = phase.game
    link = f"{settings.FRONTEND_URL}/game/{game.id}"

    def _send():
        for member in extension_members:
            if member.user_id is None:
                continue
            send_notification_to_users(
                user_ids=[member.user_id],
                title=game.name,
                body=f"You did not submit orders and used an automatic extension ({member.nmr_extensions_remaining} remaining). The current phase is extended until {deadline_str}.",
                notification_type="nmr_extension_used",
                data={"game_id": str(game.id), "link": link},
            )

        extension_ids = {m.user_id for m in extension_members if m.user_id is not None}
        other_ids = [
            user_id for user_id in game.notification_user_ids()
            if user_id not in extension_ids
        ]
        if other_ids:
            send_notification_to_users(
                user_ids=other_ids,
                title=game.name,
                body=f"Some player(s) did not submit orders and used an extension. The current phase is extended until {deadline_str}.",
                notification_type="nmr_extension_applied",
                data={"game_id": str(game.id), "link": link},
            )

    transaction.on_commit(_send)
