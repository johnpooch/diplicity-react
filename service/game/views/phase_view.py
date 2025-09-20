from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services, serializers


class PhaseResolveView(views.APIView):
    permission_classes = []

    @extend_schema(
        responses={200: serializers.PhaseResolveResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        phase_service = services.PhaseService(None)
        result = phase_service.resolve()
        serializer = serializers.PhaseResolveResponseSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)