from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from common.permissions import IsActiveOrCompletedGame, IsGameParticipant, IsChannelMember, IsNotKickedGamePlayer, IsNotKickedGameParticipant, IsNotSandboxGame, IsNotNoPressActiveGame

from .models import Channel, ChannelMember
from .permissions import CanMuteChannel, CanRenameChannel
from .serializers import ChannelSerializer, ChannelDetailSerializer, ChannelMessageSerializer, ChannelMarkReadSerializer, ChannelMuteSerializer, ChannelPreviewSerializer, ChannelUpdateSerializer
from .utils import channel_detail_fingerprint, channel_list_fingerprint, channel_preview_fingerprint
from common.views import PrecomputedConditionalGetMixin, SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin


class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsNotKickedGamePlayer, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelSerializer


class ChannelRetrieveUpdateView(
    PrecomputedConditionalGetMixin,
    SelectedGameMixin,
    SelectedChannelMixin,
    CurrentGameMemberMixin,
    generics.RetrieveUpdateAPIView,
):
    """Retrieve a channel without its message history, or rename a private channel."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), CanRenameChannel()]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ChannelDetailSerializer
        return ChannelUpdateSerializer

    def get_fingerprint(self):
        return channel_detail_fingerprint(self.get_object(), self.get_game(), self.get_current_game_member())

    def get_object(self):
        if self.request.method != "GET":
            return self.get_channel()
        if not hasattr(self, "_channel_detail"):
            user = self.request.user
            self._channel_detail = get_object_or_404(
                Channel.objects.accessible_to_member(self.get_current_game_member(), self.get_game())
                .with_unread_counts(user)
                .with_mute_state(user)
                .with_first_unread_message_id(user)
                .with_latest_message_id()
                .with_detail_data(),
                id=self.kwargs["channel_id"],
            )
        return self._channel_detail


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


class ChannelPreviewListView(PrecomputedConditionalGetMixin, SelectedGameMixin, CurrentGameMemberMixin, generics.ListAPIView):
    """List the channels the requester can read, each with only its latest message."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelPreviewSerializer

    def get_fingerprint(self):
        return channel_preview_fingerprint(self.request, self.get_game(), self.get_current_game_member())

    def get_queryset(self):
        user = self.request.user
        return (
            Channel.objects.accessible_to_member(self.get_current_game_member(), self.get_game())
            .with_unread_counts(user)
            .with_mute_state(user)
            .with_preview_data()
            .order_for_list()
        )
