from rest_framework import permissions, generics
from drf_spectacular.utils import extend_schema

from bot.models import BotProfile
from bot.serializers import AvailableBotSerializer, BotMemberCreateSerializer
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
