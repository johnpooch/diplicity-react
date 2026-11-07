from rest_framework import permissions, generics
from rest_framework.parsers import MultiPartParser
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.views import View
from drf_spectacular.utils import extend_schema

from common.permissions import CanUseBotOpponent, IsGameManager, IsPendingGame
from common.views import IMAGE_CONTENT_SECURITY_POLICY, SelectedGameMixin
from .models import UserProfile, UserProfilePicture, UserProfilePictureContent
from .serializers import (
    AddableUserSerializer,
    PublicUserProfileSerializer,
    UserProfilePictureSerializer,
    UserProfileSerializer,
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
        return UserProfile.objects.with_related_data().get(user=self.request.user)


@extend_schema(
    request={"multipart/form-data": UserProfilePictureSerializer},
    responses={200: UserProfileSerializer},
    methods=["PUT"],
)
class UserProfilePictureView(generics.UpdateAPIView, generics.DestroyAPIView):
    """Upload or remove the signed-in user's profile picture."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]
    serializer_class = UserProfilePictureSerializer
    http_method_names = ["put", "delete", "options"]

    def get_object(self):
        return UserProfile.objects.with_related_data().get(user=self.request.user)

    def perform_destroy(self, instance):
        UserProfilePicture.objects.remove_for_profiles(
            UserProfile.objects.filter(pk=instance.pk)
        )


class UserProfilePictureImageView(View):
    def get(self, request, user_id, content_hash):
        try:
            content = UserProfilePictureContent.objects.select_related("picture").get(
                picture__profile__user_id=user_id, picture__content_hash=content_hash
            )
        except UserProfilePictureContent.DoesNotExist:
            return HttpResponseNotFound()

        response = HttpResponse(content.data, content_type=content.picture.content_type)
        response["Cache-Control"] = "public, max-age=31536000, immutable"
        response["Content-Security-Policy"] = IMAGE_CONTENT_SECURITY_POLICY
        return response


class PublicUserProfileRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublicUserProfileSerializer

    def get_object(self):
        user_id = self.kwargs["user_id"]
        return get_object_or_404(
            UserProfile.objects.with_related_data().with_commitment_total(),
            user_id=user_id,
        )


class AddableUserListView(SelectedGameMixin, generics.ListAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsPendingGame,
        IsGameManager,
        CanUseBotOpponent,
    ]
    serializer_class = AddableUserSerializer

    def get_queryset(self):
        return UserProfile.objects.addable_to_game(self.get_game())


class UserAccountDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        UserProfile.objects.delete_account(instance)
