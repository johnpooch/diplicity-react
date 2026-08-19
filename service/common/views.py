from django.db import transaction
from django.shortcuts import get_object_or_404
from django.apps import apps

Phase = apps.get_model("phase", "Phase")
Game = apps.get_model("game", "Game")
Channel = apps.get_model("channel", "Channel")


def resolve_game(request, game_id, lock=False):
    cache = getattr(request, "_game_cache", None)
    if cache is None:
        cache = {}
        request._game_cache = cache
    if lock:
        cache[game_id] = get_object_or_404(Game.objects.select_for_update(), id=game_id)
    elif game_id not in cache:
        cache[game_id] = get_object_or_404(Game, id=game_id)
    return cache[game_id]


def resolve_phase(request, game_id, phase_id):
    cache = getattr(request, "_phase_cache", None)
    if cache is None:
        cache = {}
        request._phase_cache = cache
    key = (game_id, phase_id)
    if key not in cache:
        cache[key] = get_object_or_404(Phase.objects.defer("options"), id=phase_id, game_id=game_id)
    return cache[key]


class SelectedGameMixin:

    def get_game(self):
        game_id = self.kwargs.get("game_id")
        return resolve_game(self.request, game_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["game"] = self.get_game()
        return context


class SeatClaimMixin(SelectedGameMixin):

    def perform_create(self, serializer):
        with transaction.atomic():
            game = resolve_game(self.request, self.kwargs.get("game_id"), lock=True)
            self.check_permissions(self.request)
            serializer.save()
            game.start_if_full()


class SelectedPhaseMixin:

    def get_phase(self):
        game_id = self.kwargs.get("game_id")
        phase_id = self.kwargs.get("phase_id")
        return resolve_phase(self.request, game_id, phase_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["phase"] = self.get_phase()
        return context


class CurrentPhaseMixin:

    def get_phase(self):
        game_id = self.kwargs.get("game_id")
        game = resolve_game(self.request, game_id)
        return game.current_phase

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["phase"] = self.get_phase()
        return context


class SelectedChannelMixin:

    def get_channel(self):
        game_id = self.kwargs.get("game_id")
        channel_id = self.kwargs.get("channel_id")
        return get_object_or_404(Channel, id=channel_id, game_id=game_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["channel"] = self.get_channel()
        return context


class CurrentGameMemberMixin:

    def get_current_game_member(self):
        game = self.get_game()
        return game.members.filter(user=self.request.user).first()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_game_member"] = self.get_current_game_member()
        return context
