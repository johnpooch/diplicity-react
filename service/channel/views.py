from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from common.permissions import IsActiveOrCompletedGame, IsGameParticipant, IsChannelMember, IsNotKickedGamePlayer, IsNotKickedGameParticipant, IsNotSandboxGame, IsNotNoPressActiveGame

from .models import Channel, ChannelMember
from .permissions import CanMuteChannel, CanRenameChannel
from .serializers import ChannelSerializer, ChannelDetailSerializer, ChannelMessageSerializer, ChannelMarkReadSerializer, ChannelMuteSerializer, ChannelPreviewSerializer, ChannelUpdateSerializer
from .utils import channel_list_fingerprint
from common.views import ConditionalGetMixin, PrecomputedConditionalGetMixin, SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin


class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsNotKickedGamePlayer, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelSerializer


class ChannelRetrieveUpdateView(ConditionalGetMixin, SelectedGameMixin, CurrentGameMemberMixin, generics.RetrieveUpdateAPIView):
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
        user = self.request.user
        member = self.get_current_game_member()
        return (
            Channel.objects.accessible_to_member(member, game)
            .with_unread_counts(user)
            .with_mute_state(user)
            .with_requester_membership(member)
            .with_first_unread_message_id(user)
            .with_latest_message_id()
            .with_detail_data()
        )

    def get_channel(self):
        if not hasattr(self, "_channel"):
            self._channel = get_object_or_404(self.get_queryset(), id=self.kwargs["channel_id"])
        return self._channel

    def get_object(self):
        return self.get_channel()


class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsNotKickedGameParticipant, IsChannelMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelMessageSerializer


class ChannelMarkReadView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsGameParticipant, IsChannelMember]
    serializer_class = ChannelMarkReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelMuteView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    """Mute or unmute notifications for a channel."""

    permission_classes = [permissions.IsAuthenticated, CanMuteChannel]
    serializer_class = ChannelMuteSerializer

    def get_object(self):
        return ChannelMember.objects.get(
            member=self.get_current_game_member(),
            channel=self.get_channel(),
        )


class ChannelListView(PrecomputedConditionalGetMixin, SelectedGameMixin, CurrentGameMemberMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelSerializer

    def get_fingerprint(self):
        return channel_list_fingerprint(self.request, self.get_game(), self.get_current_game_member())

    def get_queryset(self):
        game = self.get_game()
        user = self.request.user
        return (
            Channel.objects.accessible_to_member(self.get_current_game_member(), game)
            .with_unread_counts(user)
            .with_mute_state(user)
            .with_related_data()
            .order_for_list()
        )


class ChannelPreviewListView(ConditionalGetMixin, SelectedGameMixin, CurrentGameMemberMixin, generics.ListAPIView):
    """List the channels the requester can read, each with only its latest message."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelPreviewSerializer

    def get_queryset(self):
        user = self.request.user
        channels = list(
            Channel.objects.accessible_to_member(self.get_current_game_member(), self.get_game())
            .with_unread_counts(user)
            .with_mute_state(user)
            .with_latest_message_id()
            .order_for_list()
        )
        Channel.objects.hydrate_latest_messages(channels)
        return channels
