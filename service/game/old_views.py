from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    DestroyAPIView,
    RetrieveAPIView,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from . import old_serializers, old_services


class GameJoinView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.GameJoinRequestSerializer

    def perform_create(self, *args, **kwargs):
        old_services.game_join(self.request.user, self.kwargs["game_id"])


class GameLeaveView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.GameLeaveRequestSerializer

    def get_object(self):
        return None

    def perform_destroy(self, *args):
        old_services.game_leave(self.request.user, self.kwargs["game_id"])


class LoginView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = old_serializers.LoginRequestSerializer

    @extend_schema(
        request=old_serializers.LoginRequestSerializer,
        responses={200: old_serializers.LoginResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        user = old_services.auth_login_or_register(data["id_token"])
        tokens = old_services.auth_get_tokens(user)

        response_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }

        output_serializer = old_serializers.LoginResponseSerializer(data=response_data)
        output_serializer.is_valid(raise_exception=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class OrderCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.OrderCreateRequestSerializer

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        old_services.order_create(
            self.request.user, self.kwargs["game_id"], validated_data
        )


class PhaseStateConfirmView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.PhaseStateConfirmSerializer

    def perform_create(self, *args):
        old_services.phase_state_confirm(self.request.user, self.kwargs["game_id"])


class VariantListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.VariantListResponseSerializer

    def get_queryset(self):
        return old_services.variant_list()


class ChannelCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.ChannelCreateRequestSerializer

    @extend_schema(
        operation_id="gameChannelCreate",
        request=old_serializers.ChannelCreateRequestSerializer,
        responses={201: old_serializers.ChannelCreateResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        game_id = self.kwargs["game_id"]
        members = data["members"]

        channel = old_services.channel_create(self.request.user, game_id, members)

        output_serializer = old_serializers.ChannelCreateResponseSerializer(
            data={"id": channel.id}
        )
        output_serializer.is_valid(raise_exception=True)

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class ChannelMessageCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.ChannelMessageCreateRequestSerializer

    @extend_schema(
        operation_id="gameChannelMessageCreate",
        request=old_serializers.ChannelMessageCreateRequestSerializer,
        responses={201: old_serializers.ChannelMessageCreateResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        game_id = self.kwargs["game_id"]
        channel_id = self.kwargs["channel_id"]
        old_services.channel_message_create(
            self.request.user,
            game_id,
            channel_id,
            serializer.validated_data,
        )


class ChannelListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.ChannelListResponseSerializer

    def get_queryset(self):
        return old_services.channel_list(self.request.user)


class UserProfileRetrieveView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = old_serializers.UserProfileSerializer

    def get_object(self):
        return self.request.user.profile
