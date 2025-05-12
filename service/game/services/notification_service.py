from fcm_django.models import FCMDevice

from .base_service import BaseService


class NotificationService(BaseService):

    def __init__(self, user):
        self.user = user

    def notify(self, user_ids, data):
        message = {
            "notification": {
                "title": data["title"],
                "body": data["message"],
            },
            "data": {
                "type": data.get("type", ""),
                "game_id": str(data.get("game_id", "")),
                "channel_id": str(data.get("channel_id", "")),
            },
        }
        devices = FCMDevice.objects.filter(user__id__in=user_ids)
        devices.send_message(message)
