from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from .serializers import (
    AppleAuthSerializer,
    EmailLoginSerializer,
    GoogleAuthSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    VerifyEmailSerializer,
)
from .utils import PasswordResetEmailRateThrottle, RegisterEmailRateThrottle


class AppleAuthView(CreateAPIView):
    serializer_class = AppleAuthSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_login"


class GoogleAuthView(CreateAPIView):
    serializer_class = GoogleAuthSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_login"


class EmailLoginView(CreateAPIView):
    serializer_class = EmailLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_login"


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle, RegisterEmailRateThrottle]
    throttle_scope = "register"


class PasswordResetView(CreateAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle, PasswordResetEmailRateThrottle]
    throttle_scope = "password_reset"


class PasswordResetConfirmView(CreateAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_confirm"


class VerifyEmailView(CreateAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verify_email"
