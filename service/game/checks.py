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
        return game_of(instance).members.seat_of(actor) is not None


class IsGameMemberCheck(Check):
    reason = "not_member"

    def check(self, instance, actor):
        if actor.pk is None:
            return False
        return any(
            member.user_id == actor.pk for member in game_of(instance).members.all()
        )


class IsActivePlayerCheck(Check):
    reason = "inactive_player"

    def check(self, instance, actor):
        member = game_of(instance).members.seat_of(actor)
        return member is not None and not member.eliminated


class IsNotSandboxGameCheck(Check):
    reason = "sandbox_game"

    def check(self, instance, actor):
        return not game_of(instance).sandbox


class IsCurrentPhaseActiveCheck(Check):
    reason = "phase_not_active"

    def check(self, instance, actor):
        phase = game_of(instance).current_phase
        return phase is not None and phase.status == PhaseStatus.ACTIVE
