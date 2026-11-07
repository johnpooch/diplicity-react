from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from common.permissions import (
    IsGameParticipant,
    IsChannelMember,
    IsNotKickedGameParticipant,
    IsNotSandboxGame,
    IsNotNoPressActiveGame,
)
from report.policies import CanModerateGamePolicy

from .models import Channel, ChannelMember, ChannelMessage
from .permissions import (
    CanCreateChannel,
    CanLeaveChannel,
    CanMuteChannel,
    CanRenameChannel,
)
from .serializers import (
    ChannelSerializer,
    ChannelDetailSerializer,
    ChannelMessageSerializer,
    ChannelMessagePageQuerySerializer,
    ChannelMessagePageSerializer,
    ChannelLeaveSerializer,
    ChannelMarkReadSerializer,
    ChannelMuteSerializer,
    ChannelPreviewSerializer,
    ChannelUpdateSerializer,
)
from common.views import (
    ConditionalGetMixin,
    PrecomputedConditionalGetMixin,
    SelectedGameMixin,
    SelectedChannelMixin,
    CurrentGameMemberMixin,
)

class ReadableChannelsMixin:
    def get_readable_channels(self):
        game = self.get_game()
        if CanModerateGamePolicy.decide(game, self.request.user):
            return Channel.objects.for_game(game)
        return Channel.objects.accessible_to_member(
            self.get_current_game_member(), game
        )


class ChannelCreateView(
    SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView
):
    permission_classes = [permissions.IsAuthenticated, CanCreateChannel]
    serializer_class = ChannelSerializer


class ChannelRetrieveUpdateView(
    PrecomputedConditionalGetMixin,
    ReadableChannelsMixin,
    SelectedGameMixin,
    CurrentGameMemberMixin,
    generics.RetrieveUpdateAPIView,
):
    """Retrieve a channel without its message history, or rename a private channel."""

    def get_fingerprint(self):
        return Channel.objects.retrieve_fingerprint(
            self.kwargs["game_id"], self.kwargs["channel_id"], self.request
        )

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), CanRenameChannel()]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ChannelDetailSerializer
        return ChannelUpdateSerializer

    def get_queryset(self):
        game = self.get_game()
        if self.request.method not in permissions.SAFE_METHODS:
            return Channel.objects.for_game(game)
        user = self.request.user
        member = self.get_current_game_member()
        return (
            self.get_readable_channels()
            .with_unread_counts(user)
            .with_mute_state(user)
            .with_requester_membership(member)
            .with_first_unread_message_id(user)
            .with_latest_message_id()
            .with_detail_data()
            .with_member_names()
        )

    def get_channel(self):
        if not hasattr(self, "_channel"):
            self._channel = get_object_or_404(
                self.get_queryset(), id=self.kwargs["channel_id"]
            )
        return self._channel

    def get_object(self):
        return self.get_channel()


@extend_schema(parameters=[ChannelMessagePageQuerySerializer])
class ChannelMessageListView(
    ReadableChannelsMixin,
    SelectedGameMixin,
    CurrentGameMemberMixin,
    generics.RetrieveAPIView,
):
    """List a page of a channel's messages, oldest to newest, bounded by message ID with `before` or `after`."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelMessagePageSerializer

    def get_object(self):
        channel = get_object_or_404(
            self.get_readable_channels(), id=self.kwargs["channel_id"]
        )
        query = ChannelMessagePageQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        return (
            ChannelMessage.objects.for_channel(channel)
            .with_sender_data()
            .page(**query.validated_data)
        )


class ChannelMessageCreateView(
    SelectedGameMixin,
    SelectedChannelMixin,
    CurrentGameMemberMixin,
    generics.CreateAPIView,
):
    permission_classes = [
        permissions.IsAuthenticated,
        IsNotKickedGameParticipant,
        IsChannelMember,
        IsNotSandboxGame,
        IsNotNoPressActiveGame,
    ]
    serializer_class = ChannelMessageSerializer


class ChannelMarkReadView(
    SelectedGameMixin,
    SelectedChannelMixin,
    CurrentGameMemberMixin,
    generics.CreateAPIView,
):
    permission_classes = [
        permissions.IsAuthenticated,
        IsGameParticipant,
        IsChannelMember,
    ]
    serializer_class = ChannelMarkReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelLeaveView(
    SelectedGameMixin,
    SelectedChannelMixin,
    CurrentGameMemberMixin,
    generics.CreateAPIView,
):
    """Leave a private channel. A member who leaves cannot rejoin."""

    permission_classes = [permissions.IsAuthenticated, CanLeaveChannel]
    serializer_class = ChannelLeaveSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelMuteView(
    SelectedGameMixin,
    SelectedChannelMixin,
    CurrentGameMemberMixin,
    generics.UpdateAPIView,
):
    """Mute or unmute notifications for a channel."""

    permission_classes = [permissions.IsAuthenticated, CanMuteChannel]
    serializer_class = ChannelMuteSerializer

    def get_object(self):
        return ChannelMember.objects.get(
            member=self.get_current_game_member(),
            channel=self.get_channel(),
        )


class ChannelPreviewListView(
    ConditionalGetMixin,
    ReadableChannelsMixin,
    SelectedGameMixin,
    CurrentGameMemberMixin,
    generics.ListAPIView,
):
    """List the channels the requester can read, each with only its latest message."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelPreviewSerializer

    def get_queryset(self):
        user = self.request.user
        channels = list(
            self.get_readable_channels()
            .with_unread_counts(user)
            .with_mute_state(user)
            .with_latest_message_id()
            .with_member_names()
            .order_for_list()
        )
        Channel.objects.hydrate_latest_messages(channels)
        return channels
