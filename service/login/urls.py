from django.urls import path

from .views import AuthView, EmailLoginView, PasswordResetConfirmView, PasswordResetView, RegisterView, VerifyEmailView

urlpatterns = [
    path("auth/login/", AuthView.as_view(), name="auth"),
    path("auth/email-login/", EmailLoginView.as_view(), name="email-login"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path("auth/password-reset/confirm/<str:uidb64>/<str:token>/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]