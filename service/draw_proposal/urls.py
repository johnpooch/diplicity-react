from django.urls import path

from . import views

urlpatterns = [
    path(
        "games/<str:game_id>/draw-proposals/",
        views.DrawProposalListView.as_view(),
        name="draw-proposal-list",
    ),
    path(
        "games/<str:game_id>/draw-proposals/create/",
        views.DrawProposalCreateView.as_view(),
        name="draw-proposal-create",
    ),
    path(
        "games/<str:game_id>/draw-proposals/<int:proposal_id>/vote/",
        views.DrawProposalVoteView.as_view(),
        name="draw-proposal-vote",
    ),
    path(
        "games/<str:game_id>/draw-proposals/<int:proposal_id>/cancel/",
        views.DrawProposalCancelView.as_view(),
        name="draw-proposal-cancel",
    ),
]
