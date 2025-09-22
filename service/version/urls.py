from django.urls import path
from . import views

urlpatterns = [
    path("version/", views.VersionRetrieveView.as_view(), name="version-retrieve"),
]