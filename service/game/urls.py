from django.urls import path

from . import views

urlpatterns = [
    path("game/", views.GameCreateView.as_view(), name="game-create"),
    path("sandbox-game/", views.CreateSandboxGameView.as_view(), name="sandbox-game-create"),
    path(
        "game/<str:game_id>/",
        views.GameRetrieveView.as_view(),
        name="game-retrieve",
    ),
    path(
        "game/<str:game_id>/clone-to-sandbox/",
        views.GameCloneToSandboxView.as_view(),
        name="game-clone-to-sandbox",
    ),
    path("games/", views.GameListView.as_view(), name="game-list"),
]
