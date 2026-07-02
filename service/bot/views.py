from rest_framework import permissions, generics
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend

from bot.filters import LLMCallFilter
from bot.models import BotProfile, LLMCall
from bot.serializers import (
    AvailableBotSerializer,
    BotMemberCreateSerializer,
    LLMCallDetailSerializer,
    LLMCallSummarySerializer,
)
from member.serializers import MemberSerializer
from common.permissions import CanUseBotOpponent, IsGameManager, IsPendingGame, IsSpaceAvailable
from common.views import SelectedGameMixin


class AvailableBotListView(SelectedGameMixin, generics.ListAPIView):
    serializer_class = AvailableBotSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameManager, CanUseBotOpponent]

    def get_queryset(self):
        return BotProfile.objects.available_for_game(self.get_game())


@extend_schema(responses={201: MemberSerializer})
class BotMemberCreateView(SelectedGameMixin, generics.CreateAPIView):
    serializer_class = BotMemberCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameManager, IsSpaceAvailable, CanUseBotOpponent]

    def perform_create(self, serializer):
        member = serializer.save()
        member.game.start_if_full()


class LLMCallBaseView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, CanUseBotOpponent]

    def get_queryset(self):
        return (
            LLMCall.objects.select_related("member__nation", "phase")
            .prefetch_related("channel__members__nation")
            .order_by("created_at")
        )


class LLMCallListView(LLMCallBaseView, generics.ListAPIView):
    serializer_class = LLMCallSummarySerializer
    filterset_class = LLMCallFilter
    filter_backends = [DjangoFilterBackend]


class LLMCallDetailView(LLMCallBaseView, generics.RetrieveAPIView):
    serializer_class = LLMCallDetailSerializer
