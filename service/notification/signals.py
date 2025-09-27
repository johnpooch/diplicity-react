from django.db.models.signals import post_save
from django.dispatch import receiver
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification
from channel.models import ChannelMessage


@receiver(post_save, sender=ChannelMessage)
def send_channel_message_notification(sender, instance, created, **kwargs):
    if created:
        if instance.channel.private:
            other_members = instance.channel.members.exclude(id=instance.sender.id)
        else:
            other_members = instance.channel.game.members.exclude(id=instance.sender.id)
        user_ids = [member.user.id for member in other_members]
        devices = FCMDevice.objects.filter(user_id__in=user_ids, active=True)

        message = Message(
            notification=Notification(
                title="New Message",
                body=f"{instance.sender.user.username} sent a message in {instance.channel.name}.",
            ),
            data={
                "type": "channel_message",
                "game_id": str(instance.channel.game.id),
                "channel_id": str(instance.channel.id),
            },
        )

        devices.send_message(message)