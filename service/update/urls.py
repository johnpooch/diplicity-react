from django.urls import path

from . import views

urlpatterns = [
    path("update/check/", views.UpdateCheckView.as_view(), name="update-check"),
]
