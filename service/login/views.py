from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import AuthSerializer, EmailLoginSerializer, PasswordResetSerializer, RegisterSerializer, VerifyEmailSerializer

User = get_user_model()


class AuthView(CreateAPIView):
    serializer_class = AuthSerializer
    permission_classes = [AllowAny]


class EmailLoginView(CreateAPIView):
    serializer_class = EmailLoginSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.to_representation(user), status=status.HTTP_200_OK)


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class PasswordResetView(CreateAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class PasswordResetConfirmView(View):
    def _get_user_and_validate_token(self, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
        if not default_token_generator.check_token(user, token):
            return None
        return user

    def get(self, request, uidb64, token):
        user = self._get_user_and_validate_token(uidb64, token)
        if user is None:
            return HttpResponse(
                "<html><body><h1>Invalid or expired link</h1>"
                "<p>This password reset link is invalid or has expired.</p></body></html>",
                status=400,
            )
        return HttpResponse(
            f'<html><body><h1>Reset Password</h1>'
            f'<form method="post">'
            f'<label>New password:<input type="password" name="new_password"></label><br>'
            f'<label>Confirm password:<input type="password" name="confirm_password"></label><br>'
            f'<button type="submit">Reset Password</button>'
            f'</form></body></html>'
        )

    def post(self, request, uidb64, token):
        user = self._get_user_and_validate_token(uidb64, token)
        if user is None:
            return HttpResponse(
                "<html><body><h1>Invalid or expired link</h1>"
                "<p>This password reset link is invalid or has expired.</p></body></html>",
                status=400,
            )
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")
        if new_password != confirm_password:
            return HttpResponse(
                "<html><body><h1>Passwords do not match</h1>"
                "<p>Please go back and try again.</p></body></html>",
                status=400,
            )
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return HttpResponse(
            "<html><body><h1>Password reset successful</h1>"
            "<p>Your password has been updated. You can now sign in.</p></body></html>"
        )


class VerifyEmailView(CreateAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)