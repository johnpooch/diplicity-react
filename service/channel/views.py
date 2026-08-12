from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from common.permissions import IsActiveOrCompletedGame, IsGameMember, IsChannelMember, IsNotKickedGameMember, IsNotSandboxGame, IsNotNoPressActiveGame

from .models import Channel, ChannelMember
from .serializers import (
    ChannelCreateSerializer,
    ChannelMarkReadSerializer,
    ChannelMessageSerializer,
    ChannelPreviewSerializer,
    ChannelRetrieveSerializer,
    ChannelUnreadSerializer,
    GameUnreadSerializer,
)
from common.views import SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin


class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    """Create a private channel between the current member and the given members."""

    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsNotKickedGameMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelCreateSerializer


class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    """Send a message to a channel as the current member."""

    permission_classes = [permissions.IsAuthenticated, IsNotKickedGameMember, IsChannelMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelMessageSerializer


class ChannelMarkReadView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    """Mark every message in a channel as read for the current member."""

    permission_classes = [permissions.IsAuthenticated, IsGameMember, IsChannelMember]
    serializer_class = ChannelMarkReadSerializer

    def get_object(self):
        return get_object_or_404(
            ChannelMember,
            member=self.get_current_game_member(),
            channel=self.get_channel(),
        )


class ChannelListView(SelectedGameMixin, generics.ListAPIView):
    """List the channels of a game visible to the current user, with a preview of the latest message."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelPreviewSerializer

    def get_queryset(self):
        game = self.get_game()
        user = self.request.user
        return (
            Channel.objects.accessible_to_user(user, game)
            .with_preview_data()
            .order_for_list()
        )


@extend_schema_view(
    get=extend_schema(
        parameters=[OpenApiParameter("cursor", str, required=False)],
    ),
)
class ChannelRetrieveView(SelectedGameMixin, SelectedChannelMixin, generics.RetrieveAPIView):
    """Retrieve a channel with a cursor-paginated page of its messages."""

    permission_classes = [permissions.AllowAny, IsChannelMember]
    serializer_class = ChannelRetrieveSerializer

    def get_object(self):
        return self.get_channel()


class ChannelUnreadRetrieveView(generics.RetrieveAPIView):
    """Retrieve the total number of unread channel messages for the current user in a game."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChannelUnreadSerializer

    def get_object(self):
        row = (
            ChannelMember.objects.unread_counts_by_game(self.request.user)
            .filter(channel__game_id=self.kwargs.get("game_id"))
            .first()
        )
        return row or {"total_unread_message_count": 0}


class GameUnreadListView(generics.ListAPIView):
    """List the current user's games that have unread channel messages, with their unread counts."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameUnreadSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            ChannelMember.objects.unread_counts_by_game(self.request.user)
            .filter(total_unread_message_count__gt=0)
            .order_by("channel__game_id")
        )
