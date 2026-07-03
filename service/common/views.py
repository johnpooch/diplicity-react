from django.shortcuts import get_object_or_404
from django.apps import apps

Phase = apps.get_model("phase", "Phase")
Game = apps.get_model("game", "Game")
Channel = apps.get_model("channel", "Channel")


def resolve_game(request, game_id):
    """Fetch the Game once per request, regardless of how many permission
    classes and mixins ask for it. Several views combine 2-3 permission
    checks + a mixin (e.g. orders create chains IsActiveGame +
    IsActiveGameMember + CurrentPhaseMixin), each of which would otherwise
    issue an independent SELECT against game_game."""
    cache = getattr(request, "_game_cache", None)
    if cache is None:
        cache = {}
        request._game_cache = cache
    if game_id not in cache:
        cache[game_id] = get_object_or_404(Game, id=game_id)
    return cache[game_id]


def resolve_phase(request, game_id, phase_id):
    """Cache the Phase fetch per request alongside resolve_game."""
    cache = getattr(request, "_phase_cache", None)
    if cache is None:
        cache = {}
        request._phase_cache = cache
    key = (game_id, phase_id)
    if key not in cache:
        cache[key] = get_object_or_404(Phase.objects.defer("options"), id=phase_id, game_id=game_id)
    return cache[key]


class SelectedGameMixin:
    """
    Used by views that have a game parameter in the URL. Provides a get_game
    method that returns the game object. Also adds game to the serializer context.
    """

    def get_game(self):
        game_id = self.kwargs.get("game_id")
        return resolve_game(self.request, game_id)

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
        return resolve_phase(self.request, game_id, phase_id)

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
        game = resolve_game(self.request, game_id)
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
        return game.members.filter(user=self.request.user).first()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_game_member"] = self.get_current_game_member()
        return context
