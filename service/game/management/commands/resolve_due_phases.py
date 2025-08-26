import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from game.models import Game, Phase
from game.services.game_service import GameService
from game.services.adjudication_service import AdjudicationService

logger = logging.getLogger("game.management.resolve_due_phases")

class Command(BaseCommand):
    help = "Resolves all game phases that are due for resolution."

    def handle(self, *args, **options):
        now = timezone.now()
        due_phases = Phase.objects.filter(
            scheduled_resolution__lte=now,
            status=Phase.ACTIVE,
        )
        if not due_phases.exists():
            self.stdout.write(self.style.SUCCESS("No due phases to resolve."))
            return

        for phase in due_phases:
            game = phase.game
            logger.info(f"Resolving phase for game {game.id} (phase {phase.id})...")
            try:
                adjudication_service = AdjudicationService(None)
                GameService(user=None, adjudication_service=adjudication_service).resolve(game.id)
                self.stdout.write(self.style.SUCCESS(f"Resolved phase for game {game.id}"))
            except Exception as e:
                logger.error(f"Failed to resolve phase for game {game.id}: {e}")
                self.stdout.write(self.style.ERROR(f"Failed to resolve phase for game {game.id}: {e}")) 