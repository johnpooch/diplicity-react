from django.core.management.base import BaseCommand

from member.models import CommitmentEntry


class Command(BaseCommand):
    def handle(self, *args, **options):
        entries = CommitmentEntry.objects.rebuild()
        players = {entry.member.user_id for entry in entries}

        self.stdout.write(
            self.style.SUCCESS(
                f"Rebuilt {len(entries)} commitment entries for {len(players)} player(s)."
            )
        )
