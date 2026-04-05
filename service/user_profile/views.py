from rest_framework import permissions, generics

from member.models import Member
from common.constants import GameStatus
from .models import UserProfile
from .serializers import PublicUserProfileSerializer, UserProfileSerializer


class PublicUserProfileRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublicUserProfileSerializer

    def get_object(self):
        return generics.get_object_or_404(
            UserProfile.objects.with_related_data(), user_id=self.kwargs["user_id"]
        )


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


class UserAccountDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        user_members = Member.objects.filter(user=instance)
        user_members.filter(game__status=GameStatus.PENDING).delete()
        user_members.filter(
            game__status__in=[GameStatus.ACTIVE, GameStatus.COMPLETED]
        ).update(kicked=True)
        instance.delete()
