from firebase_admin.messaging import Message, Notification
from fcm_django.models import FCMDevice
from django.contrib.auth.models import User

from .base_service import BaseService


class NotificationService(BaseService):

    def __init__(self, user):
        self.user = user

    def notify(self, user_ids, data):
        devices = FCMDevice.objects.filter(user__id__in=user_ids)

        devices.send_message(
            Message(
                notification=Notification(
                    title=data["title"],
                    body=data["body"],
                ),
                data={
                    "type": data.get("type", ""),
                    "game_id": str(data.get("game_id", "")),
                    "channel_id": str(data.get("channel_id", "")),
                },
            )
        )
