from django.shortcuts import get_object_or_404
from django.db.models import Count, OuterRef, Q, Subquery
from django.apps import apps
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from opentelemetry import trace

ChannelMember = apps.get_model("channel", "ChannelMember")

from common.constants import GameStatus
from .models import Game
from .serializers import (
    GameCreateSerializer,
    GameCreateSandboxSerializer,
    GameCloneToSandboxSerializer,
    GameFindSimilarSerializer,
    GameListSerializer,
    GameRetrieveSerializer,
    GamePauseSerializer,
    GameUnpauseSerializer,
    GameExtendDeadlineSerializer,
)
from common.views import SelectedGameMixin
from common.serializers import EmptySerializer
from common.permissions import IsActiveGame, IsGameMember, IsGameMaster, IsSandboxGame
from common.pagination import StandardPageNumberPagination
from .filters import GameFilter

tracer = trace.get_tracer(__name__)


class GameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GameRetrieveSerializer

    queryset = Game.objects.all().with_retrieve_data()

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.kwargs.get("game_id"))


def _bulk_unread_counts(game_ids, user):
    ChannelMessage = apps.get_model("channel", "ChannelMessage")
    last_read_subq = ChannelMember.objects.filter(
        channel=OuterRef("channel_id"),
        member__user=user,
    ).values("last_read_at")[:1]
    rows = (
        ChannelMessage.objects.filter(
            channel__game_id__in=game_ids,
            channel__member_channels__member__user=user,
            created_at__gt=Subquery(last_read_subq),
        )
        .distinct()
        .values("channel__game_id")
        .annotate(count=Count("id"))
    )
    return {str(row["channel__game_id"]): row["count"] for row in rows}


class GameListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GameListSerializer
    filterset_class = GameFilter
    filter_backends = [DjangoFilterBackend]
    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        queryset = Game.objects.all().with_list_data().order_by("-created_at")

        if "sandbox" not in self.request.query_params and "mine" not in self.request.query_params:
            queryset = queryset.filter(sandbox=False)

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(private=False)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        games = list(page) if page is not None else list(queryset)

        if request.user.is_authenticated and games:
            unread = _bulk_unread_counts([g.id for g in games], request.user)
            for game in games:
                game._unread_message_count = unread.get(str(game.id), 0)
        else:
            for game in games:
                game._unread_message_count = 0

        serializer = self.get_serializer(games, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class GameCreateView(generics.CreateAPIView):
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
            Game.objects.with_list_data()
            .filter(
                status=GameStatus.PENDING,
                private=False,
                sandbox=False,
                variant_id=variant,
                movement_phase_duration=duration,
            )
            .exclude(members__user=request.user)
        )

        if not candidates:
            return Response({"game": None})

        candidates.sort(
            key=lambda g: (
                g.variant.nations.count() - g.members.count(),
                -g.created_at.timestamp(),
            )
        )
        match_data = GameListSerializer(candidates[0], context={"request": request}).data
        return Response({"game": match_data})


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


class GameDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, IsSandboxGame, IsGameMember]

    def get_object(self):
        return self.get_game()


class GameExtendDeadlineView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMaster]
    serializer_class = GameExtendDeadlineSerializer

    def get_object(self):
        return self.get_game()
