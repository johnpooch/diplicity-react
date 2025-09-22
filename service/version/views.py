from rest_framework import permissions, generics
from rest_framework.response import Response

from .serializers import VersionSerializer
from .utils import get_version_data


class VersionRetrieveView(generics.GenericAPIView):
    permission_classes = []
    serializer_class = VersionSerializer

    def get(self, request, *args, **kwargs):
        version_data = get_version_data()
        serializer = self.get_serializer(version_data)
        return Response(serializer.data)
