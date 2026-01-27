from rest_framework import permissions, generics
from common.permissions import IsActiveOrCompletedGame, IsGameMember, IsChannelMember, IsNotSandboxGame

from .models import Channel
from .serializers import ChannelSerializer, ChannelMessageSerializer
from common.views import SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin


class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsGameMember, IsNotSandboxGame]
    serializer_class = ChannelSerializer


class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsGameMember, IsChannelMember, IsNotSandboxGame]
    serializer_class = ChannelMessageSerializer


class ChannelListView(SelectedGameMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame]
    serializer_class = ChannelSerializer

    def get_queryset(self):
        return Channel.objects.accessible_to_user(self.request.user, self.get_game()).with_related_data()
