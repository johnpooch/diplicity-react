from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from django.apps import apps
from common.constants import GameStatus, PressType
from common.views import resolve_game

Game = apps.get_model("game", "Game")
Channel = apps.get_model("channel", "Channel")


class IsActiveGame(BasePermission):

    message = "This game is not active."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        return game.status == GameStatus.ACTIVE


class IsActiveOrCompletedGame(BasePermission):

    message = "This game is not active or finished."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        return game.status in (GameStatus.ACTIVE, GameStatus.COMPLETED, GameStatus.ABANDONED)


class IsGameMember(BasePermission):
    message = "User is not a member of the game."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        return game.members.filter(user=request.user).exists()


class IsGameMemberOrGameMaster(BasePermission):
    message = "User is not a member of the game."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        if game.game_master_id is not None and game.game_master_id == request.user.id:
            return True
        return game.members.filter(user=request.user).exists()


class IsActiveGameMember(BasePermission):
    message = "User cannot perform this action."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))

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
        game = resolve_game(request, view.kwargs.get("game_id"))
        return game.status == GameStatus.PENDING


class IsNotGameMember(BasePermission):
    message = "User is already a member of the game."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        return not game.members.filter(user=request.user).exists()


class IsSpaceAvailable(BasePermission):
    message = "Game already has the maximum number of players."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        return game.members.count() < game.variant.nations.count()


class IsCurrentPhaseActive(BasePermission):
    message = "Current phase is not active."

    def has_permission(self, request, view):
        from common.constants import PhaseStatus

        game = resolve_game(request, view.kwargs.get("game_id"))
        current_phase = game.phases.last()
        return current_phase and current_phase.status == PhaseStatus.ACTIVE


class IsUserPhaseStateExists(BasePermission):
    message = "No phase state found for user."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
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
        game = resolve_game(request, view.kwargs.get("game_id"))
        return game.sandbox


class IsNotSandboxGame(BasePermission):
    message = "This action is not available for sandbox games."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        return not game.sandbox


class IsNotNoPressActiveGame(BasePermission):
    message = "Messaging is not available in active No Press games."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        if game.press_type != PressType.NO_PRESS:
            return True
        return game.status in (GameStatus.COMPLETED, GameStatus.ABANDONED)


class IsPendingPublicChannelOrActiveGame(BasePermission):
    message = "Channel access is not available for this game."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        if game.status in (GameStatus.ACTIVE, GameStatus.COMPLETED, GameStatus.ABANDONED):
            return True
        if game.status == GameStatus.PENDING:
            channel_id = view.kwargs.get("channel_id")
            if channel_id is None:
                return True
            channel = Channel.objects.filter(id=channel_id).first()
            if channel is None:
                return True
            return not channel.private
        return False


class IsGameManager(BasePermission):
    message = "Only the game creator can perform this action."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        if game.game_master_id is not None:
            self.message = "Only the game master can perform this action."
            return game.game_master_id == request.user.id
        if not game.members.filter(user=request.user).exists():
            self.message = "User is not a member of the game."
            return False
        if game.created_by_id is None or game.created_by_id != request.user.id:
            self.message = "Only the game creator can perform this action."
            return False
        return True


class IsNotGameMaster(BasePermission):
    message = "The game master cannot join the game as a player."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        return game.game_master_id is None or game.game_master_id != request.user.id


class CanDeleteGame(BasePermission):
    message = "You cannot delete this game."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        return game.can_delete(request.user)


class IsInCivilDisorder(BasePermission):
    message = "Player is not in civil disorder."

    def has_permission(self, request, view):
        game = resolve_game(request, view.kwargs.get("game_id"))
        member = game.members.filter(user=request.user).first()
        if not member:
            self.message = "User is not a member of the game."
            return False
        return member.civil_disorder
