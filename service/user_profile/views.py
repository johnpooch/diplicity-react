from rest_framework import permissions, generics
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from game.models import Game
from member.models import Member
from phase.models import PhaseState
from common.constants import GameStatus, PhaseStatus
from common.permissions import CanUseBotOpponent, IsGameManager, IsPendingGame
from common.views import SelectedGameMixin
from .models import UserProfile
from .serializers import AddableUserSerializer, UserProfileSerializer, PublicUserProfileSerializer


class UserProfileRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return UserProfile.objects.with_related_data().get(user=self.request.user)


class UserProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)


class PublicUserProfileRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublicUserProfileSerializer

    def get_object(self):
        user_id = self.kwargs["user_id"]
        return get_object_or_404(UserProfile.objects.with_related_data(), user_id=user_id)


class AddableUserListView(SelectedGameMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameManager, CanUseBotOpponent]
    serializer_class = AddableUserSerializer

    def get_queryset(self):
        return UserProfile.objects.addable_to_game(self.get_game())


@extend_schema(exclude=True)
class LegacyAvailableBotListView(AddableUserListView):
    """Serves GET /game/<id>/available-bots/ for mobile builds shipped before the
    endpoint was renamed. Kept out of the schema so codegen only ever emits the
    current path. Remove once those builds are out of circulation."""


class UserAccountDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        with transaction.atomic():
            user_members = Member.objects.filter(user=instance)
            pending_game_ids = list(
                user_members.filter(game__status=GameStatus.PENDING).values_list(
                    "game_id", flat=True
                )
            )
            user_members.filter(game__status=GameStatus.PENDING).delete()
            ongoing_members = user_members.filter(
                game__status__in=[GameStatus.ACTIVE, GameStatus.COMPLETED]
            )
            ongoing_members.update(kicked=True)
            PhaseState.objects.filter(
                member__in=ongoing_members, phase__status=PhaseStatus.ACTIVE
            ).update(has_possible_orders=False)
            for game in Game.objects.filter(id__in=pending_game_ids):
                game.delete_if_empty_pending()
            instance.delete()
