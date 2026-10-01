from rest_framework import permissions, generics, status
from rest_framework.response import Response
from common.permissions import IsActiveOrCompletedGame, IsGameParticipant, IsChannelMember, IsNotKickedGamePlayer, IsNotKickedGameParticipant, IsNotSandboxGame, IsNotNoPressActiveGame

from .models import Channel, ChannelMember
from .permissions import CanMuteChannel, CanRenameChannel
from .serializers import ChannelSerializer, ChannelMessageSerializer, ChannelMarkReadSerializer, ChannelMuteSerializer, ChannelUpdateSerializer
from common.views import ConditionalGetMixin, SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin


class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsNotKickedGamePlayer, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelSerializer


class ChannelUpdateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    """Rename a private channel."""

    permission_classes = [
        permissions.IsAuthenticated,
        CanRenameChannel,
    ]
    serializer_class = ChannelUpdateSerializer

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


class ChannelListView(ConditionalGetMixin, SelectedGameMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelSerializer

    def get_current_game_member(self):
        if not hasattr(self, "_current_game_member"):
            user = self.request.user
            self._current_game_member = (
                self.get_game().members.filter(user=user).first()
                if user.is_authenticated
                else None
            )
        return self._current_game_member

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_game_member"] = self.get_current_game_member()
        return context

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
