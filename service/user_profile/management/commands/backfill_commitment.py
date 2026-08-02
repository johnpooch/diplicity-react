from django.core.management.base import BaseCommand

from user_profile.commitment import recompute_commitment
from user_profile.models import UserProfile


class Command(BaseCommand):
    def handle(self, *args, **options):
        profiles = UserProfile.objects.select_related("user")
        count = 0
        for profile in profiles.iterator():
            recompute_commitment(profile.user)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Recomputed commitment for {count} player(s)."))
