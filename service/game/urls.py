from django.urls import path

from . import views

urlpatterns = [
    path("game/", views.GameCreateView.as_view(), name="game-create"),
    path(
        "game/<str:game_id>/",
        views.GameRetrieveView.as_view(),
        name="game-retrieve",
    ),
    path("games/", views.GameListView.as_view(), name="game-list"),
]
