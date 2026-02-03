from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from django.apps import apps
from common.constants import GameStatus

Game = apps.get_model("game", "Game")
Channel = apps.get_model("channel", "Channel")


class IsActiveGame(BasePermission):

    message = "This game is not active."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return game.status == GameStatus.ACTIVE


class IsActiveOrCompletedGame(BasePermission):

    message = "This game is not active or finished."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return game.status in (GameStatus.ACTIVE, GameStatus.COMPLETED, GameStatus.ABANDONED)


class IsGameMember(BasePermission):
    message = "User is not a member of the game."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return game.members.filter(user=request.user).exists()


class IsActiveGameMember(BasePermission):
    message = "User cannot perform this action."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)

        member = game.members.filter(user=request.user).first()
        if not member:
            self.message = "User is not a member of the game."
            return False

        if member.eliminated:
            self.message = "Cannot perform action for eliminated players."
            return False

        if member.kicked:
            self.message = "Cannot perform action for kicked players."
            return False

        return True


class IsChannelMember(BasePermission):
    message = "User is not a member of the channel."

    def has_permission(self, request, view):
        channel_id = view.kwargs.get("channel_id")
        channel = get_object_or_404(Channel, id=channel_id)
        if channel.private:
            return channel.members.filter(user=request.user).exists()
        else:
            return True


class IsPendingGame(BasePermission):
    message = "Game is not in pending status."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return game.status == GameStatus.PENDING


class IsNotGameMember(BasePermission):
    message = "User is already a member of the game."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return not game.members.filter(user=request.user).exists()


class IsSpaceAvailable(BasePermission):
    message = "Game already has the maximum number of players."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return game.members.count() < game.variant.nations.count()


class IsCurrentPhaseActive(BasePermission):
    message = "Current phase is not active."

    def has_permission(self, request, view):
        from common.constants import PhaseStatus

        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        current_phase = game.phases.last()
        return current_phase and current_phase.status == PhaseStatus.ACTIVE


class IsUserPhaseStateExists(BasePermission):
    message = "No phase state found for user."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        member = game.members.filter(user=request.user).first()
        if not member:
            return False
        current_phase = game.phases.last()
        if not current_phase:
            return False
        return current_phase.phase_states.filter(member=member).exists()


class IsSandboxGame(BasePermission):
    message = "This action is only available for sandbox games."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return game.sandbox


class IsNotSandboxGame(BasePermission):
    message = "This action is not available for sandbox games."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return not game.sandbox


class IsGameMaster(BasePermission):
    """
    Permission that verifies the user is the Game Master of the game.
    Note: This also implicitly verifies membership - no need to combine with IsGameMember.
    """
    message = "Only the Game Master can perform this action."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        member = game.members.filter(user=request.user).first()
        if not member:
            self.message = "User is not a member of the game."
            return False
        if not member.is_game_master:
            self.message = "Only the Game Master can perform this action."
            return False
        return True
