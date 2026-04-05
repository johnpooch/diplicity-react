from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from opentelemetry import trace

from .models import Game
from .serializers import (
    GameCreateSerializer,
    GameCreateSandboxSerializer,
    GameCloneToSandboxSerializer,
    GameListSerializer,
    GameRetrieveSerializer,
    GamePauseSerializer,
    GameUnpauseSerializer,
    GameExtendDeadlineSerializer,
)
from common.views import SelectedGameMixin
from common.permissions import IsActiveGame, IsGameMember, IsGameMaster
from common.pagination import StandardPageNumberPagination
from .filters import GameFilter

tracer = trace.get_tracer(__name__)


class GameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GameRetrieveSerializer

    queryset = Game.objects.all().with_retrieve_data()

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.kwargs.get("game_id"))


class GameListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GameListSerializer
    filterset_class = GameFilter
    filter_backends = [DjangoFilterBackend]
    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        queryset = Game.objects.all().with_list_data().order_by("-created_at")

        if "sandbox" not in self.request.query_params:
            queryset = queryset.filter(sandbox=False)

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(private=False)

        return queryset


class GameCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameCreateSerializer


class CreateSandboxGameView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameCreateSandboxSerializer


class GameCloneToSandboxView(SelectedGameMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMember]
    serializer_class = GameCloneToSandboxSerializer


class GamePauseView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMaster]
    serializer_class = GamePauseSerializer

    def get_object(self):
        return self.get_game()


class GameUnpauseView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMaster]
    serializer_class = GameUnpauseSerializer

    def get_object(self):
        return self.get_game()


class GameExtendDeadlineView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMaster]
    serializer_class = GameExtendDeadlineSerializer

    def get_object(self):
        return self.get_game()
