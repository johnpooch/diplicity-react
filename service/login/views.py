from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .serializers import AuthSerializer


class AuthView(CreateAPIView):
    serializer_class = AuthSerializer
    permission_classes = [AllowAny]