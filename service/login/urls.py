from django.urls import path

from .views import AuthView, EmailLoginView, RegisterView, VerifyEmailView

urlpatterns = [
    path("auth/login/", AuthView.as_view(), name="auth"),
    path("auth/email-login/", EmailLoginView.as_view(), name="email-login"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
]