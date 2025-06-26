from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services, serializers


class VariantListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: serializers.VariantSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        variant_service = services.VariantService(request.user)
        variants = variant_service.list()
        serializer = serializers.VariantSerializer(variants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
