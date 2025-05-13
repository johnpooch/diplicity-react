from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import OptionsSerializer


class OptionsRetrieveView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: OptionsSerializer},
    )
    def get(self, request, game_id, *args, **kwargs):
        options_service = services.OptionsService(request.user)
        options = options_service.retrieve(game_id)
        serializer = OptionsSerializer(options)
        return Response(serializer.data, status=status.HTTP_200_OK)
