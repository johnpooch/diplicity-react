from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from update.serializers import UpdateCheckResponseSerializer, UpdateCheckSerializer


@extend_schema(responses={201: UpdateCheckResponseSerializer})
class UpdateCheckView(generics.CreateAPIView):
    """
    Serves the self-hosted update protocol of @capgo/capacitor-updater. Returns
    the newest active bundle the caller's native binary can run, or a body with
    no url key when there is nothing to install.
    """

    permission_classes = [AllowAny]
    serializer_class = UpdateCheckSerializer
