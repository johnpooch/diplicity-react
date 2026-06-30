from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from fcm_django.models import FCMDevice


class NotificationDeviceViewSet(FCMDeviceAuthorizedViewSet):
    def perform_create(self, serializer):
        self._deactivate_other_active_devices(serializer)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._deactivate_other_active_devices(serializer)
        super().perform_update(serializer)

    def _deactivate_other_active_devices(self, serializer):
        if not serializer.validated_data.get("active", True):
            return

        device_type = serializer.validated_data["type"]
        other_active_devices = FCMDevice.objects.filter(
            user=self.request.user, type=device_type, active=True
        )
        if serializer.instance is not None:
            other_active_devices = other_active_devices.exclude(id=serializer.instance.id)

        other_active_devices.deactivate(
            reason="new_token_registered",
            source="notification_device_viewset",
        )
