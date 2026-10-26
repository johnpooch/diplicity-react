from common.checks import Check
from common.constants import GameStatus, PhaseStatus


class IsActiveGameCheck(Check):
    reason = "game_not_active"

    def check(self, instance, actor):
        return instance.game.status == GameStatus.ACTIVE


class IsGamePlayerCheck(Check):
    reason = "not_player"

    def check(self, instance, actor):
        return instance.game.members.players().filter(user_id=actor.pk).exists()


class IsActivePlayerCheck(Check):
    reason = "inactive_player"

    def check(self, instance, actor):
        members = instance.game.members.players().filter(user_id=actor.pk)
        return any(not member.eliminated and member.occupied for member in members)


class IsNotSandboxGameCheck(Check):
    reason = "sandbox_game"

    def check(self, instance, actor):
        return not instance.game.sandbox


class IsCurrentPhaseActiveCheck(Check):
    reason = "phase_not_active"

    def check(self, instance, actor):
        phase = instance.game.current_phase
        return phase is not None and phase.status == PhaseStatus.ACTIVE
