from rest_framework import generics

from .serializers import VersionSerializer
from .utils import get_version_data


class VersionRetrieveView(generics.RetrieveAPIView):
    permission_classes = []
    serializer_class = VersionSerializer

    def get_object(self):
        return get_version_data()
