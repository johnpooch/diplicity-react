from rest_framework import permissions, generics
from django.shortcuts import get_object_or_404

from .models import Member
from .serializers import MemberSerializer
from common.permissions import IsPendingGame, IsNotGameMember, IsSpaceAvailable, IsGameMember
from common.views import SelectedGameMixin
from game import services


class MemberCreateView(SelectedGameMixin, generics.CreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsNotGameMember, IsSpaceAvailable]

    def perform_create(self, serializer):
        member = serializer.save()

        # Auto-start game logic if at capacity
        if member.game.variant.nations.count() == member.game.members.count():
            adjudication_service = services.AdjudicationService(self.request.user)
            game_service = services.GameService(self.request.user, adjudication_service)
            game_service.start(member.game.id)


class MemberDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameMember]

    def get_object(self):
        game = self.get_game()
        return get_object_or_404(Member, game=game, user=self.request.user)
