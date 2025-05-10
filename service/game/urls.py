from django.urls import path

from . import old_views
from . import views

urlpatterns = [
    path("auth/login/", old_views.LoginView.as_view(), name="auth-login"),
    path("variants/", old_views.VariantListView.as_view(), name="variant-list"),
    path("game/", views.GameCreateView.as_view(), name="game-create"),
    path("game/<int:game_id>/join/", views.GameJoinView.as_view(), name="game-join"),
    path(
        "game/<int:game_id>/leave/",
        views.GameLeaveView.as_view(),
        name="game-leave",
    ),
    path(
        "game/<int:game_id>/order/",
        old_views.OrderCreateView.as_view(),
        name="order-create",
    ),
    path(
        "game/<int:game_id>/confirm/",
        old_views.PhaseStateConfirmView.as_view(),
        name="phase-state-confirm",
    ),
    path(
        "game/<int:game_id>/",
        views.GameRetrieveView.as_view(),
        name="game-retrieve",
    ),
    path("games/", views.GameListView.as_view(), name="game-list"),
    path(
        "game/<int:game_id>/channel/",
        old_views.ChannelCreateView.as_view(),
        name="channel-create",
    ),
    path(
        "game/<int:game_id>/channel/<int:channel_id>/",
        old_views.ChannelMessageCreateView.as_view(),
        name="channel-message-create",
    ),
    path(
        "game/<int:game_id>/channels/",
        old_views.ChannelListView.as_view(),
        name="channel-list",
    ),
    path("user/", old_views.UserProfileRetrieveView.as_view(), name="user-profile"),
]
