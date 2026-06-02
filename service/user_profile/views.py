from rest_framework import permissions, generics
from django.db import transaction

from game.models import Game
from member.models import Member
from common.constants import GameStatus
from .models import UserProfile
from .serializers import UserProfileSerializer


class UserProfileRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return UserProfile.objects.with_related_data().get(user=self.request.user)


class UserProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return UserProfile.objects.with_related_data().get(user=self.request.user)


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
            user_members.filter(
                game__status__in=[GameStatus.ACTIVE, GameStatus.COMPLETED]
            ).update(kicked=True)
            for game in Game.objects.filter(id__in=pending_game_ids):
                game.delete_if_empty_pending()
            instance.delete()
