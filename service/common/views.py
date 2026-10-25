import hashlib

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.apps import apps
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.http import conditional_page
from rest_framework import generics, status
from rest_framework.response import Response

from common.constants import PhaseStatus
from common.etag import if_none_match

Phase = apps.get_model("phase", "Phase")
Game = apps.get_model("game", "Game")
Channel = apps.get_model("channel", "Channel")

COMPLETED_PHASE_MAX_AGE = 60 * 60 * 24 * 7


def resolve_game(request, game_id, lock=False):
    """Fetch the Game once per request, regardless of how many permission
    classes and mixins ask for it. Several views combine 2-3 permission
    checks + a mixin (e.g. orders create chains IsActiveGame +
    IsActiveGameMember + CurrentPhaseMixin), each of which would otherwise
    issue an independent SELECT against game_game.

    Pass lock=True to re-fetch the row FOR UPDATE and replace what the cache
    holds, so checks that re-run after it see committed state rather than the
    snapshot the request started from."""
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


class SeatClaimMixin(SelectedGameMixin):

    def perform_create(self, serializer):
        with transaction.atomic():
            game = resolve_game(self.request, self.kwargs.get("game_id"), lock=True)
            self.check_permissions(self.request)
            serializer.save()
            game.start_if_full()


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
        if not hasattr(self, "_current_game_member"):
            user = self.request.user
            self._current_game_member = (
                self.get_game().members.filter(user=user).first() if user.is_authenticated else None
            )
        return self._current_game_member

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_game_member"] = self.get_current_game_member()
        return context


class ConditionalGetMixin:

    @method_decorator(conditional_page)
    @method_decorator(cache_control(private=True, no_cache=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class PrecomputedConditionalGetMixin:

    def get_fingerprint(self):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        etag = f'"{self.get_fingerprint()}"'
        if if_none_match(request, etag):
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
        else:
            response = super().get(request, *args, **kwargs)
        response["ETag"] = etag
        response["Cache-Control"] = "private, no-cache"
        return response


class CompletedPhaseCacheMixin:

    completed_phase_etag_salt = None

    def get(self, request, *args, **kwargs):
        phase = self.get_phase()
        if phase.status != PhaseStatus.COMPLETED or resolve_game(request, self.kwargs.get("game_id")).sandbox:
            return super().get(request, *args, **kwargs)
        digest = hashlib.sha256(f"{self.completed_phase_etag_salt}|{phase.id}".encode()).hexdigest()
        etag = f'"{digest[:32]}"'
        if if_none_match(request, etag):
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
        else:
            response = super().get(request, *args, **kwargs)
        response["ETag"] = etag
        response["Cache-Control"] = f"private, max-age={COMPLETED_PHASE_MAX_AGE}"
        return response


class LoaderMixin:
    output_serializer_class = None

    def get_serializer_class(self):
        return self.output_serializer_class

    def get_loader(self):
        return self.output_serializer_class.loader(self.request.user)

    def get_queryset(self):
        if self.queryset is not None:
            return super().get_queryset()
        return self.get_loader().get_queryset()

    def render_instance(self, instance, status_code=status.HTTP_200_OK):
        instance = self.get_loader().load(instance.pk)
        return Response(self.get_serializer(instance).data, status=status_code)


class LoadedRetrieveView(LoaderMixin, generics.RetrieveAPIView):

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_loader().hydrate([self.get_object()])[0]
        return Response(self.get_serializer(instance).data)


class LoadedListView(LoaderMixin, generics.ListAPIView):

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        rows = self.get_loader().hydrate(page if page is not None else queryset)
        data = self.get_serializer(rows, many=True).data
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)


class LoadedFirstView(LoaderMixin, generics.GenericAPIView):
    result_key = None

    def get(self, request, *args, **kwargs):
        instance = self.filter_queryset(self.get_queryset()).first()
        data = None
        if instance is not None:
            data = self.get_serializer(self.get_loader().hydrate([instance])[0]).data
        return Response({self.result_key: data})


class CommandMixin(LoaderMixin):
    command = None
    input_serializer_class = None

    def get_target(self):
        if (self.lookup_url_kwarg or self.lookup_field) not in self.kwargs:
            return None
        return self.get_object()

    def run_command(self):
        target = self.get_target()
        data = {}
        if self.input_serializer_class is not None:
            serializer = self.input_serializer_class(data=self.request.data, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
        return self.command(actor=self.request.user, **data)(target)


class CommandCreateView(CommandMixin, generics.GenericAPIView):

    def post(self, request, *args, **kwargs):
        return self.render_instance(self.run_command(), status.HTTP_201_CREATED)


class CommandUpdateView(CommandMixin, generics.GenericAPIView):

    def put(self, request, *args, **kwargs):
        return self.render_instance(self.run_command())

    def patch(self, request, *args, **kwargs):
        return self.render_instance(self.run_command())


class CommandDestroyView(CommandMixin, generics.GenericAPIView):

    def delete(self, request, *args, **kwargs):
        self.run_command()
        return Response(status=status.HTTP_204_NO_CONTENT)
