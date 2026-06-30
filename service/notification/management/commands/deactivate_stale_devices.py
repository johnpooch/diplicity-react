from django.core.management.base import BaseCommand
from django.db.models import Max


class Command(BaseCommand):
    def handle(self, *args, **options):
        from fcm_django.models import FCMDevice

        latest_active_ids = (
            FCMDevice.objects.filter(active=True, user__isnull=False)
            .values("user_id", "type")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )

        stale_devices = FCMDevice.objects.filter(active=True, user__isnull=False).exclude(
            id__in=list(latest_active_ids)
        )
        count = stale_devices.count()
        stale_devices.deactivate(
            reason="stale_duplicate_token_cleanup",
            source="deactivate_stale_devices_command",
        )

        self.stdout.write(self.style.SUCCESS(f"Deactivated {count} stale device(s)."))
