from django.urls import path

from .views import AuthView

urlpatterns = [
    path("auth/login/", AuthView.as_view(), name="auth"),
]