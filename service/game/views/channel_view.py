from rest_framework import status, views, permissions, serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import ChannelSerializer


class ChannelCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class ChannelCreateRequestSerializer(serializers.Serializer):
        members = serializers.ListField(child=serializers.IntegerField(), required=True)

    @extend_schema(
        request=ChannelCreateRequestSerializer,
        responses={201: ChannelSerializer},
    )
    def post(self, request, game_id, *args, **kwargs):
        serializer = self.ChannelCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        channel_service = services.ChannelService(request.user)
        channel = channel_service.create(game_id, validated_data)

        response_serializer = ChannelSerializer(channel)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ChannelMessageCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class ChannelMessageCreateRequestSerializer(serializers.Serializer):
        body = serializers.CharField(required=True, max_length=1000)

    @extend_schema(
        request=ChannelMessageCreateRequestSerializer,
        responses={201: ChannelSerializer},
    )
    def post(self, request, game_id, channel_id, *args, **kwargs):
        serializer = self.ChannelMessageCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        channel_service = services.ChannelService(request.user)
        channel_service.create_message(game_id, channel_id, validated_data)
        channel = channel_service.retrieve(game_id, channel_id)

        response_serializer = ChannelSerializer(channel)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ChannelListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: ChannelSerializer(many=True)},
    )
    def get(self, request, game_id, *args, **kwargs):
        channel_service = services.ChannelService(request.user)
        channels = channel_service.list(game_id)

        serializer = ChannelSerializer(channels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
