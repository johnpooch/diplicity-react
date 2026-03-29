from rest_framework import permissions, generics, status
from rest_framework.response import Response
from common.permissions import IsActiveOrCompletedGame, IsGameMember, IsChannelMember, IsNotSandboxGame

from .models import Channel
from .serializers import ChannelSerializer, ChannelMessageSerializer, ChannelMarkReadSerializer
from common.views import SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin


class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsGameMember, IsNotSandboxGame]
    serializer_class = ChannelSerializer


class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsGameMember, IsChannelMember, IsNotSandboxGame]
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
        return (
            Channel.objects.accessible_to_user(self.request.user, self.get_game())
            .with_unread_counts(self.request.user)
            .with_related_data()
        )
