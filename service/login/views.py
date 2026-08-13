from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .serializers import (
    AppleAuthSerializer,
    EmailLoginSerializer,
    GoogleAuthSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    VerifyEmailSerializer,
)


class AppleAuthView(CreateAPIView):
    serializer_class = AppleAuthSerializer
    permission_classes = [AllowAny]


class GoogleAuthView(CreateAPIView):
    serializer_class = GoogleAuthSerializer
    permission_classes = [AllowAny]


class EmailLoginView(CreateAPIView):
    serializer_class = EmailLoginSerializer
    permission_classes = [AllowAny]


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class PasswordResetView(CreateAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]


class PasswordResetConfirmView(CreateAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]


class VerifyEmailView(CreateAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]
