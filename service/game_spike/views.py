from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions

from common.pagination import StandardPageNumberPagination
from common.policies import allows
from common.views import (
    CommandCreateView,
    CommandDestroyView,
    CommandUpdateView,
    ConditionalGetMixin,
    LoadedFirstView,
    LoadedListView,
    LoadedRetrieveView,
)

from .commands import (
    CloneGameToSandbox,
    CreateGame,
    CreateSandboxGame,
    DeleteGame,
    ExtendGameDeadline,
    PauseGame,
    UnpauseGame,
)
from .filters import FastestGameFilter, GameFilter, MyCurrentGamesFilter, MyFinishedGamesFilter, SimilarGameFilter
from .models import Game
from .serializers import (
    GameCreateSandboxSerializer,
    GameCreateSerializer,
    GameExtendDeadlineSerializer,
    GameListSerializer,
    GameRetrieveSerializer,
    MyGameSerializer,
    MyGamesCurrentSerializer,
)


class GameRetrieveView(ConditionalGetMixin, LoadedRetrieveView):
    """Return a game with the requesting user's decisions about it."""

    permission_classes = [permissions.AllowAny]
    lookup_url_kwarg = "game_id"
    output_serializer_class = GameRetrieveSerializer


class GameListView(LoadedListView):
    """List games, newest first unless another ordering is requested."""

    permission_classes = [permissions.AllowAny]
    output_serializer_class = GameListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = GameFilter
    pagination_class = StandardPageNumberPagination


class MyGamesCurrentView(LoadedListView):
    """Return the authenticated user's current games, grouped into ordered sections, each game with a single state."""

    permission_classes = [permissions.IsAuthenticated]
    output_serializer_class = MyGamesCurrentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MyCurrentGamesFilter
    pagination_class = None


class MyGamesFinishedView(LoadedListView):
    """Return the authenticated user's finished and departed games, newest first by when each game ended for them."""

    permission_classes = [permissions.IsAuthenticated]
    output_serializer_class = MyGameSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MyFinishedGamesFilter
    pagination_class = StandardPageNumberPagination


class GameFindSimilarView(LoadedFirstView):
    """Return the joinable game with the given variant and phase length that is closest to starting."""

    permission_classes = [permissions.IsAuthenticated]
    output_serializer_class = GameListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SimilarGameFilter
    result_key = "game"


class GameFastestView(LoadedFirstView):
    """Return the joinable game closest to starting whose movement phases last 24 hours or longer."""

    permission_classes = [permissions.IsAuthenticated]
    output_serializer_class = GameListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = FastestGameFilter
    result_key = "game"


class GameCreateView(CommandCreateView):
    """Create a game from a variant's starting position, seating the creator."""

    permission_classes = [permissions.IsAuthenticated]
    input_serializer_class = GameCreateSerializer
    command = CreateGame
    output_serializer_class = GameRetrieveSerializer


class GameCreateSandboxView(CommandCreateView):
    """Create a started sandbox game in which the creator plays every nation."""

    permission_classes = [permissions.IsAuthenticated]
    input_serializer_class = GameCreateSandboxSerializer
    command = CreateSandboxGame
    output_serializer_class = GameRetrieveSerializer


class GameCloneToSandboxView(CommandCreateView):
    """Copy the current position of a game into a new sandbox game for the requesting player."""

    permission_classes = [permissions.IsAuthenticated, allows("can_clone_to_sandbox")]
    lookup_url_kwarg = "game_id"
    command = CloneGameToSandbox
    output_serializer_class = GameRetrieveSerializer


class GamePauseView(CommandUpdateView):
    """Pause an active game."""

    permission_classes = [permissions.IsAuthenticated, allows("can_pause")]
    lookup_url_kwarg = "game_id"
    command = PauseGame
    output_serializer_class = GameRetrieveSerializer


class GameUnpauseView(CommandUpdateView):
    """Resume a paused game, pushing the current deadline back by the time spent paused."""

    permission_classes = [permissions.IsAuthenticated, allows("can_unpause")]
    lookup_url_kwarg = "game_id"
    command = UnpauseGame
    output_serializer_class = GameRetrieveSerializer


class GameExtendDeadlineView(CommandUpdateView):
    """Push the current phase's deadline back by the given duration."""

    permission_classes = [permissions.IsAuthenticated, allows("can_extend_deadline")]
    lookup_url_kwarg = "game_id"
    input_serializer_class = GameExtendDeadlineSerializer
    command = ExtendGameDeadline
    output_serializer_class = GameRetrieveSerializer


class GameDeleteView(CommandDestroyView):
    """Delete a game that has not started, or one of the requesting user's sandbox games."""

    permission_classes = [permissions.IsAuthenticated, allows("can_delete")]
    lookup_url_kwarg = "game_id"
    queryset = Game.objects.all()
    command = DeleteGame
