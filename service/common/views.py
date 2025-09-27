from django.shortcuts import get_object_or_404
from django.apps import apps

Phase = apps.get_model("phase", "Phase")
Game = apps.get_model("game", "Game")
Channel = apps.get_model("channel", "Channel")


class SelectedGameMixin:
    """
    Used by views that have a game parameter in the URL. Provides a get_game
    method that returns the game object. Also adds game to the serializer context.
    """

    def get_game(self):
        game_id = self.kwargs.get("game_id")
        return get_object_or_404(Game, id=game_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["game"] = self.get_game()
        return context


class SelectedPhaseMixin:
    """
    Used by views that have a phase parameter in the URL. Provides a get_phase
    method that returns the phase object. Also adds phase to the serializer context.
    """

    def get_phase(self):
        game_id = self.kwargs.get("game_id")
        phase_id = self.kwargs.get("phase_id")
        return get_object_or_404(Phase, id=phase_id, game_id=game_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["phase"] = self.get_phase()
        return context


class CurrentPhaseMixin:
    """
    Used by views that have a game parameter in the URL. Provides a get_phase
    method that returns the current phase for the game. Also adds phase to the serializer context.
    """

    def get_phase(self):
        game_id = self.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return game.current_phase

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["phase"] = self.get_phase()
        return context


class SelectedChannelMixin:
    """
    Used by views that have a channel parameter in the URL. Provides a get_channel
    method that returns the channel object. Also adds channel to the serializer context.
    """

    def get_channel(self):
        game_id = self.kwargs.get("game_id")
        channel_id = self.kwargs.get("channel_id")
        return get_object_or_404(Channel, id=channel_id, game_id=game_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["channel"] = self.get_channel()
        return context


class CurrentGameMemberMixin:
    """
    Used by views that have a game parameter in the URL. Provides a get_current_game_member
    method that returns the user's member for the game. Also adds game member to the serializer context.
    """

    def get_current_game_member(self):
        game = self.get_game()
        return game.members.get(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_game_member"] = self.get_current_game_member()
        return context
