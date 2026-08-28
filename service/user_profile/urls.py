from django.urls import path
from . import views

urlpatterns = [
    path("user/", views.UserProfileRetrieveView.as_view(), name="user-profile"),
    path("user/update/", views.UserProfileUpdateView.as_view(), name="user-profile-update"),
    path("user/delete/", views.UserAccountDeleteView.as_view(), name="user-delete"),
    path("user/picture/", views.UserProfilePictureView.as_view(), name="user-picture"),
    path(
        "users/<int:user_id>/picture/<str:content_hash>",
        views.UserProfilePictureImageView.as_view(),
        name="user-picture-image",
    ),
    path("users/<int:user_id>/", views.PublicUserProfileRetrieveView.as_view(), name="public-user-profile"),
    path("game/<str:game_id>/addable-user/", views.AddableUserListView.as_view(), name="game-addable-user-list"),
    path("game/<str:game_id>/available-bots/", views.LegacyAvailableBotListView.as_view(), name="game-available-bots-legacy"),
]
