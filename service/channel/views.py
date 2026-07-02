from rest_framework import permissions, generics, status
from rest_framework.response import Response
from common.permissions import IsActiveOrCompletedGame, IsGameMember, IsChannelMember, IsNotSandboxGame, IsNotNoPressActiveGame

from .models import Channel
from .serializers import ChannelSerializer, ChannelMessageSerializer, ChannelMarkReadSerializer
from common.views import SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin


class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsGameMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelSerializer


class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsGameMember, IsChannelMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelMessageSerializer


class ChannelMarkReadView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsGameMember, IsChannelMember]
    serializer_class = ChannelMarkReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelListView(SelectedGameMixin, generics.ListAPIView):
    permission_classes = [IsActiveOrCompletedGame]
    serializer_class = ChannelSerializer

    def get_queryset(self):
        game = self.get_game()
        user = self.request.user
        member = game.members.filter(user=user).first() if user.is_authenticated else None
        return (
            Channel.objects.accessible_to_user(user, game)
            .with_unread_counts(user)
            .with_bot_membership()
            .with_member_message_count(member, game.current_phase)
            .with_related_data()
            .order_for_list()
        )
