from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from common.constants import GameStatus
from .loaders import GameListLoader
from .models import Game
from .service import MyGamesService
from .serializers import (
    GameCreateSerializer,
    GameCreateSandboxSerializer,
    GameCloneToSandboxSerializer,
    GameFastestSerializer,
    GameFindSimilarSerializer,
    GameListSerializer,
    GameRetrieveSerializer,
    GamePauseSerializer,
    GameUnpauseSerializer,
    GameExtendDeadlineSerializer,
    MyGamesCurrentSerializer,
    MyGameSerializer,
)
from common.views import (
    LoaderDetailView,
    LoaderListView,
    PrecomputedConditionalGetMixin,
    RefusalMixin,
    SelectedGameMixin,
    resolve_game,
)
from common.serializers import EmptySerializer
from common.permissions import IsActiveGame, IsGamePlayer, IsGameManager, CanDeleteGame
from common.pagination import StandardPageNumberPagination
from emit import emit
from .filters import GameFilter


class GameRetrieveView(PrecomputedConditionalGetMixin, LoaderDetailView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GameRetrieveSerializer
    lookup_field = "id"
    lookup_url_kwarg = "game_id"

    def get_fingerprint(self):
        return Game.objects.retrieve_fingerprint(
            self.kwargs.get("game_id"), self.request
        )


class GameListView(LoaderListView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GameListSerializer
    filterset_class = GameFilter
    filter_backends = [DjangoFilterBackend]
    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset().order_by("-created_at")

        if (
            "sandbox" not in self.request.query_params
            and "mine" not in self.request.query_params
        ):
            queryset = queryset.filter(sandbox=False)

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(private=False)

        return queryset


class MyGamesCurrentView(generics.RetrieveAPIView):
    """Return the authenticated user's current games, grouped into ordered sections, each game with a single state."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyGamesCurrentSerializer

    def get_object(self):
        return MyGamesService(self.request.user).current()


class MyGamesFinishedView(generics.ListAPIView):
    """Return the authenticated user's finished and departed games, newest first by when each game ended for them."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyGameSerializer
    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        return MyGamesService(self.request.user).finished()


class GameCreateView(RefusalMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameCreateSerializer


class GameFindSimilarView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameFindSimilarSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("variant", str, required=True),
            OpenApiParameter("movement_phase_duration", str, required=True),
        ],
        responses=GameFindSimilarSerializer,
    )
    def get(self, request):
        variant = request.query_params.get("variant")
        duration = request.query_params.get("movement_phase_duration")
        if not variant or not duration:
            return Response({"game": None})

        candidates = list(
            GameListLoader.get_queryset(request.user)
            .filter(
                status=GameStatus.PENDING,
                private=False,
                sandbox=False,
                variant_id=variant,
                movement_phase_duration=duration,
            )
            .exclude_mine(request.user)
            .with_zero_unread_counts()
        )

        if not candidates:
            return Response({"game": None})

        candidates.sort(
            key=lambda g: (
                g.variant.nations.filter(non_playable=False).count()
                - g.members.count(),
                -g.created_at.timestamp(),
            )
        )
        [match] = GameListLoader.hydrate(candidates[:1], request.user)
        match_data = GameListSerializer(match, context={"request": request}).data
        return Response({"game": match_data})


class GameFastestView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameFastestSerializer

    @extend_schema(responses=GameFastestSerializer)
    def get(self, request):
        """Return the joinable game closest to starting whose movement phases last 24 hours or longer."""
        game = Game.objects.fastest_start(request.user)
        game_data = None
        if game is not None:
            [game] = GameListLoader.hydrate(
                GameListLoader.get_queryset(request.user)
                .filter(pk=game.pk)
                .with_zero_unread_counts(),
                request.user,
            )
            game_data = GameListSerializer(game, context={"request": request}).data
        return Response({"game": game_data})


class CreateSandboxGameView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameCreateSandboxSerializer


class GameCloneToSandboxView(SelectedGameMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGamePlayer]
    serializer_class = GameCloneToSandboxSerializer


class GamePauseView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameManager]
    serializer_class = GamePauseSerializer

    def get_object(self):
        return self.get_game()


class GameUnpauseView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameManager]
    serializer_class = GameUnpauseSerializer

    def get_object(self):
        return self.get_game()


class GameDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, CanDeleteGame]

    def get_object(self):
        return self.get_game()

    def perform_destroy(self, instance):
        with transaction.atomic():
            game = resolve_game(self.request, self.kwargs.get("game_id"), lock=True)
            self.check_permissions(self.request)
            is_game_master_delete = (
                not game.sandbox
                and game.game_master_id is not None
                and game.game_master_id == self.request.user.id
            )
            user_ids = list(game.seated_member_user_ids())
            game_name = game.name
            game.delete()
        if is_game_master_delete:
            emit(
                "game_deleted",
                recipients=user_ids,
                game_name=game_name,
                actor=self.request.user,
            )


class GameExtendDeadlineView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameManager]
    serializer_class = GameExtendDeadlineSerializer

    def get_object(self):
        return self.get_game()
