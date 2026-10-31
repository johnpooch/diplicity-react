from django.db.models import Prefetch

from common.loaders import Loader
from phase.models import Phase

from .models import DrawProposal


class DrawProposalLoader(Loader):
    queryset = DrawProposal.objects.select_related(
        "game",
        "created_by__user__profile__uploaded_picture",
        "created_by__nation",
        "phase",
    ).prefetch_related(
        Prefetch(
            "game__phases", queryset=Phase.objects.only("id", "game_id", "ordinal")
        ),
        "votes",
    )
