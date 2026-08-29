from rest_framework import permissions, generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from common.permissions import IsActiveOrCompletedGame, IsGameMember, IsChannelMember, IsNotKickedGameMember, IsNotSandboxGame, IsNotNoPressActiveGame

from .models import Channel
from .serializers import ChannelSerializer, ChannelCreateSerializer, ChannelMessageSerializer, ChannelMarkReadSerializer
from common.views import SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin


@extend_schema(request=ChannelCreateSerializer, responses={201: ChannelSerializer})
class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame, IsNotKickedGameMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelCreateSerializer


class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsNotKickedGameMember, IsChannelMember, IsNotSandboxGame, IsNotNoPressActiveGame]
    serializer_class = ChannelMessageSerializer


class ChannelMarkReadView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsGameMember, IsChannelMember]
    serializer_class = ChannelMarkReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelListView(SelectedGameMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ChannelSerializer

    def get_queryset(self):
        game = self.get_game()
        user = self.request.user
        return (
            Channel.objects.accessible_to_user(user, game)
            .with_unread_counts(user)
            .with_related_data()
            .order_for_list()
        )
