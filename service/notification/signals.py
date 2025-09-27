import logging
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification
from channel.models import ChannelMessage
from game.models import Game
from common.constants import GameStatus, PhaseStatus
from phase.models import Phase

logger = logging.getLogger(__name__)


def send_notification_to_users(user_ids, title, body, notification_type, data=None):
    if not user_ids:
        return

    devices = FCMDevice.objects.filter(user_id__in=user_ids, active=True)
    if not devices.exists():
        return

    message_data = data or {}
    message_data["type"] = notification_type

    message = Message(
        notification=Notification(title=title, body=body),
        data=message_data,
    )

    try:
        devices.send_message(message)
        logger.info(f"Sent {notification_type} notification to {len(user_ids)} users")
    except Exception as e:
        logger.error(f"Failed to send {notification_type} notification: {str(e)}")


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

        user_ids = [member.user.id for member in other_members]

        send_notification_to_users(
            user_ids=user_ids,
            title="New Message",
            body=f"{instance.sender.user.username} sent a message in {instance.channel.name}.",
            notification_type="channel_message",
            data={
                "game_id": str(instance.channel.game.id),
                "channel_id": str(instance.channel.id),
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
            user_ids = [member.user.id for member in instance.members.all()]

            send_notification_to_users(
                user_ids=user_ids,
                title="Game Started",
                body=f"Game '{instance.name}' has started!",
                notification_type="game_start",
                data={"game_id": str(instance.id)},
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
            user_ids = [member.user.id for member in instance.game.members.all()]

            send_notification_to_users(
                user_ids=user_ids,
                title="Phase Resolved",
                body=f"Phase '{instance.name}' has been resolved!",
                notification_type="phase_resolved",
                data={"game_id": str(instance.game.id)},
            )

        transaction.on_commit(send_notification)
