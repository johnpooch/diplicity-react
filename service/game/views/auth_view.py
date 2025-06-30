import logging
from rest_framework import status, views, permissions, serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import AuthSerializer


logger = logging.getLogger("game")

class AuthLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    class AuthLoginRequestSerializer(serializers.Serializer):
        id_token = serializers.CharField()

    @extend_schema(
        request=AuthLoginRequestSerializer,
        responses={200: AuthSerializer},
    )
    def post(self, request, *args, **kwargs):
        logger.info(f"AuthLoginView.post called")
        serializer = self.AuthLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        auth_service = services.AuthService()
        logger.info(f"AuthService initialized")
        user, tokens = auth_service.login_or_register(validated_data["id_token"])
        logger.info(f"Login or register completed")

        response_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }

        logger.info(f"Serializing response")
        response_serializer = AuthSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        logger.info(f"Response serialized, returning response")
        return Response(response_serializer.data, status=status.HTTP_200_OK)
