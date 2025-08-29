from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import OptionSerializer, ListOptionsRequestSerializer


class OptionsListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: OptionSerializer(many=True)},
        request=ListOptionsRequestSerializer,
    )
    def post(self, request, game_id, phase_id, *args, **kwargs):
        option_service = services.OptionService(request.user)
        options = option_service.get_options_for_order(game_id, phase_id, request.data.get("order", {}))
        
        serializer = OptionSerializer(options, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
