from django.urls import path
from .views import (
    DrawProposalListView,
    DrawProposalCreateView,
    DrawProposalVoteUpdateView,
    DrawProposalCancelView,
)

urlpatterns = [
    path(
        "games/<str:game_id>/draw-proposals/",
        DrawProposalListView.as_view(),
        name="draw-proposal-list",
    ),
    path(
        "games/<str:game_id>/draw-proposals/create/",
        DrawProposalCreateView.as_view(),
        name="draw-proposal-create",
    ),
    path(
        "games/<str:game_id>/draw-proposals/<int:proposal_id>/vote/",
        DrawProposalVoteUpdateView.as_view(),
        name="draw-proposal-vote",
    ),
    path(
        "games/<str:game_id>/draw-proposals/<int:proposal_id>/cancel/",
        DrawProposalCancelView.as_view(),
        name="draw-proposal-cancel",
    ),
]
