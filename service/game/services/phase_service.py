import logging
from django.utils import timezone
from ..models import Game
from phase.models import Phase
from .game_service import GameService
from .adjudication_service import AdjudicationService
from .base_service import BaseService
from common.constants import PhaseStatus

logger = logging.getLogger("game.services.phase")


class PhaseService(BaseService):
    def __init__(self, user):
        self.user = user

    def resolve(self):
        """Resolves all game phases that are due for resolution."""
        now = timezone.now()
        due_phases = Phase.objects.filter(
            scheduled_resolution__lte=now,
            status=PhaseStatus.ACTIVE,
        )

        resolved_count = 0
        failed_count = 0
        errors = []

        for phase in due_phases:
            game = phase.game
            logger.info(f"Resolving phase for game {game.id} (phase {phase.id})...")
            try:
                adjudication_service = AdjudicationService(None)
                GameService(user=None, adjudication_service=adjudication_service).resolve(game.id)
                resolved_count += 1
                logger.info(f"Resolved phase for game {game.id}")
            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to resolve phase for game {game.id}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        return {
            "resolved": resolved_count,
            "failed": failed_count
        }