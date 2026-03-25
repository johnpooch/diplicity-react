from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import AuthSerializer, RegisterSerializer, VerifyEmailSerializer


class AuthView(CreateAPIView):
    serializer_class = AuthSerializer
    permission_classes = [AllowAny]


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class VerifyEmailView(CreateAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)