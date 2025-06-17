from django.urls import path

from . import views

urlpatterns = [
    path("auth/login/", views.AuthLoginView.as_view(), name="auth-login"),
    path("game/", views.GameCreateView.as_view(), name="game-create"),
    path("game/<str:game_id>/join/", views.GameJoinView.as_view(), name="game-join"),
    path(
        "game/<str:game_id>/leave/",
        views.GameLeaveView.as_view(),
        name="game-leave",
    ),
    path(
        "game/<str:game_id>/confirm/",
        views.GameConfirmPhaseView.as_view(),
        name="game-confirm-phase",
    ),
    path(
        "game/<str:game_id>/",
        views.GameRetrieveView.as_view(),
        name="game-retrieve",
    ),
    path("games/", views.GameListView.as_view(), name="game-list"),
    path(
        "game/<str:game_id>/channel/",
        views.ChannelCreateView.as_view(),
        name="channel-create",
    ),
    path(
        "game/<str:game_id>/channel/<int:channel_id>/",
        views.ChannelMessageCreateView.as_view(),
        name="channel-message-create",
    ),
    path(
        "game/<str:game_id>/channels/",
        views.ChannelListView.as_view(),
        name="channel-list",
    ),
    path("user/", views.UserProfileRetrieveView.as_view(), name="user-profile"),
    path("variants/", views.VariantListView.as_view(), name="variant-list"),
    path(
        "game/<str:game_id>/order/",
        views.OrderCreateView.as_view(),
        name="order-create",
    ),
    path(
        "game/<str:game_id>/phase/<int:phase_id>/orders/",
        views.OrderListView.as_view(),
        name="order-list",
    ),
    path("version/", views.VersionRetrieveView.as_view(), name="version-retrieve"),
]
