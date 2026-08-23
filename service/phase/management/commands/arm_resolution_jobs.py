from django.core.management.base import BaseCommand

from phase.models import Phase


class Command(BaseCommand):
    help = "Arm a resolution job for every active phase in a live game that is missing one."

    def handle(self, *args, **options):
        armed = Phase.objects.backfill_resolution_jobs()
        self.stdout.write(self.style.SUCCESS(f"Armed resolution jobs for {armed} phases."))
