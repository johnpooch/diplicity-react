from django.urls import path
from . import views

urlpatterns = [
    path(
        "game/<str:game_id>/confirm-phase/",
        views.PhaseStateUpdateView.as_view(),
        name="game-confirm-phase",
    ),
    path(
        "game/<str:game_id>/phase-states/",
        views.PhaseStateListView.as_view(),
        name="phase-state-list",
    ),
    path(
        "game/<str:game_id>/resolve-phase/",
        views.PhaseResolveView.as_view(),
        name="game-resolve-phase",
    ),
    path("phase/resolve/", views.PhaseResolveAllView.as_view(), name="phase-resolve-all"),
]
