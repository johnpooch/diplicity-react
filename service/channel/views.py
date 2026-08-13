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
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsNotKickedGameMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelCreateSerializer


class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsNotKickedGameMember, IsChannelMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelMessageSerializer


class ChannelMarkReadView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsGameMember, IsChannelMember]
    serializer_class = ChannelMarkReadSerializer

    def get_object(self):
        return get_object_or_404(
            ChannelMember,
            member=self.get_current_game_member(),
            channel=self.get_channel(),
        )


class ChannelListView(SelectedGameMixin, generics.ListAPIView):
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
    permission_classes = [permissions.AllowAny, IsChannelMember]
    serializer_class = ChannelRetrieveSerializer

    def get_object(self):
        return self.get_channel()


class ChannelUnreadRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChannelUnreadSerializer

    def get_object(self):
        rows = list(
            ChannelMember.objects.unread_counts_by_channel(self.request.user)
            .filter(channel__game_id=self.kwargs.get("game_id"))
            .filter(unread_message_count__gt=0)
        )
        return {
            "total_unread_message_count": sum(row["unread_message_count"] for row in rows),
            "channels": rows,
        }


class GameUnreadListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameUnreadSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            ChannelMember.objects.unread_counts_by_game(self.request.user)
            .filter(total_unread_message_count__gt=0)
            .order_by("channel__game_id")
        )
