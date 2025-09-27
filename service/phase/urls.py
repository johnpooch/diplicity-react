from django.urls import path
from . import views

urlpatterns = [
    path(
        "game/<str:game_id>/confirm-phase/",
        views.PhaseStateUpdateView.as_view(),
        name="game-confirm-phase",
    ),
    path(
        "game/<str:game_id>/phase-state/",
        views.PhaseStateRetrieveView.as_view(),
        name="phase-state-retrieve",
    ),
    path("phase/resolve/", views.PhaseResolveView.as_view(), name="phase-resolve"),
]
