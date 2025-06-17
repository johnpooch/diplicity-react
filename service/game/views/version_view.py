from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services, serializers


class VersionRetrieveView(views.APIView):

    @extend_schema(
        responses={200: serializers.VersionSerializer},
    )
    def get(self, request, *args, **kwargs):
        version_data = services.VersionService().get()
        serializer = serializers.VersionSerializer(version_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
