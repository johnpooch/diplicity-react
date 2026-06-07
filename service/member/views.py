from rest_framework import permissions, generics
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from .models import Member
from .serializers import MemberSerializer
from common.serializers import EmptySerializer
from common.permissions import IsPendingGame, IsNotGameMember, IsSpaceAvailable, IsGameMember, IsGameMaster
from common.views import SelectedGameMixin
from notification.tasks import send_notification


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

    def perform_destroy(self, instance):
        game = instance.game
        with transaction.atomic():
            super().perform_destroy(instance)
            game.delete_if_empty_pending()


class MemberKickView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameMaster]

    def get_object(self):
        game = self.get_game()
        member = get_object_or_404(Member, game=game, id=self.kwargs["member_id"])
        if member.user == self.request.user:
            self.permission_denied(self.request, message="Cannot kick yourself from the game.")
        return member

    def perform_destroy(self, instance):
        game = instance.game
        user_id = instance.user_id
        with transaction.atomic():
            instance.delete()
            if user_id:
                send_notification.defer(
                    user_ids=[user_id],
                    title=game.name,
                    body="You were removed from this game by the game creator.",
                    notification_type="kicked_from_staging",
                    data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
                )
