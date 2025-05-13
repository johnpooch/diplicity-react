import json
from rest_framework import exceptions
from .. import models
from .base_service import BaseService


class OptionsService(BaseService):
    def __init__(self, user):
        self.user = user

    def retrieve(self, game_id):
        try:
            # Get the game and verify it's active
            game = models.Game.objects.get(id=game_id)
            if game.status != models.Game.ACTIVE:
                raise exceptions.ValidationError("Game is not active")

            # Get current phase
            current_phase = game.current_phase
            if not current_phase:
                raise exceptions.ValidationError("Game has no phases")

            # Find the member for this user
            try:
                member = models.Member.objects.get(game=game, user=self.user)
            except models.Member.DoesNotExist:
                return {'options': None}

            # Get the phase state for this member and phase
            try:
                phase_state = models.PhaseState.objects.get(
                    member=member,
                    phase=current_phase
                )
                # Convert the stored JSON string to a dictionary
                options = json.loads(phase_state.options) if phase_state.options else None
                return {'options': options}
            except models.PhaseState.DoesNotExist:
                return {'options': None}

        except models.Game.DoesNotExist:
            raise exceptions.NotFound("Game not found")
