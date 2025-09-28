from rest_framework import permissions, generics
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from .models import Member
from .serializers import MemberSerializer
from common.serializers import EmptySerializer
from common.permissions import IsPendingGame, IsNotGameMember, IsSpaceAvailable, IsGameMember
from common.views import SelectedGameMixin


class MemberCreateView(SelectedGameMixin, generics.CreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsNotGameMember, IsSpaceAvailable]

    @extend_schema(request=EmptySerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        member = serializer.save()
        if member.game.variant.nations.count() == member.game.members.count():
            member.game.start()


class MemberDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameMember]

    def get_object(self):
        game = self.get_game()
        return get_object_or_404(Member, game=game, user=self.request.user)
