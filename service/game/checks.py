from common.checks import Check
from common.constants import GameStatus, PhaseStatus

from .models import Game


def game_of(instance):
    return instance if isinstance(instance, Game) else instance.game


class IsActiveGameCheck(Check):
    reason = "game_not_active"

    def check(self, instance, actor):
        return game_of(instance).status == GameStatus.ACTIVE


class IsGamePlayerCheck(Check):
    reason = "not_player"

    def check(self, instance, actor):
        return game_of(instance).members.players().filter(user_id=actor.pk).exists()


class IsActivePlayerCheck(Check):
    reason = "inactive_player"

    def check(self, instance, actor):
        members = game_of(instance).members.players().filter(user_id=actor.pk)
        return any(not member.eliminated and member.occupied for member in members)


class IsNotSandboxGameCheck(Check):
    reason = "sandbox_game"

    def check(self, instance, actor):
        return not game_of(instance).sandbox


class IsCurrentPhaseActiveCheck(Check):
    reason = "phase_not_active"

    def check(self, instance, actor):
        phase = game_of(instance).current_phase
        return phase is not None and phase.status == PhaseStatus.ACTIVE
