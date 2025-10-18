from django.urls import path
from . import views

urlpatterns = [
    path("user/", views.UserProfileRetrieveView.as_view(), name="user-profile"),
    path("user/update/", views.UserProfileUpdateView.as_view(), name="user-profile-update"),
]