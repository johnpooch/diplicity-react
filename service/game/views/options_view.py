from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import OptionSerializer


class ListOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: OptionSerializer(many=True)},
    )
    def get(self, request, game_id, phase_id, *args, **kwargs):
        """
        List the provinces that the player can order for in the current phase.
        """
        option_service = services.OptionService(request.user)
        options = option_service.list(game_id, phase_id)

        serializer = OptionSerializer(options, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
