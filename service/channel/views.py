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

from .loaders import ChannelLoader, ChannelMessageLoader
from .models import Channel, ChannelMember
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
    LoaderListView,
    LoaderMixin,
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

    def perform_create(self, serializer):
        super().perform_create(serializer)
        serializer.instance = ChannelLoader.get(
            serializer.instance.pk, self.request.user
        )


class ChannelRetrieveUpdateView(
    ConditionalGetMixin,
    LoaderMixin,
    ReadableChannelsMixin,
    SelectedGameMixin,
    CurrentGameMemberMixin,
    generics.RetrieveUpdateAPIView,
):
    """Retrieve a channel without its message history, or rename a private channel."""

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
        readable = self.get_readable_channels()
        return (
            self.get_loader()
            .get_queryset(self.request.user)
            .filter(pk__in=readable.values("pk"))
        )

    def get_channel(self):
        if not hasattr(self, "_channel"):
            self._channel = get_object_or_404(
                self.get_queryset(), id=self.kwargs["channel_id"]
            )
        return self._channel

    def get_object(self):
        return self.get_channel()

    def retrieve(self, request, *args, **kwargs):
        [channel] = self.get_loader().hydrate([self.get_object()], request.user)
        return Response(self.get_serializer(channel).data)


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
        page = (
            ChannelMessageLoader.get_queryset(self.request.user)
            .for_channel(channel)
            .page(**query.validated_data)
        )
        page["results"] = ChannelMessageLoader.hydrate(
            page["results"], self.request.user
        )
        return page


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

    def perform_create(self, serializer):
        super().perform_create(serializer)
        serializer.instance = ChannelMessageLoader.get(
            serializer.instance.pk, self.request.user
        )


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
    LoaderListView,
):
    """List the channels the requester can read, each with only its latest message."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelPreviewSerializer

    def get_queryset(self):
        readable = self.get_readable_channels()
        return (
            super()
            .get_queryset()
            .filter(pk__in=readable.values("pk"))
            .order_for_list()
        )
