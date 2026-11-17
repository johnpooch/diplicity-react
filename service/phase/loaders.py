from common.loaders import Loader

from .hydrators import PhaseStateMemberHydrator, ProvinceNationsHydrator
from .models import Phase, PhaseState


class PhaseStateLoader(Loader):
    queryset = PhaseState.objects.select_related(
        "phase",
        "member__game",
        "member__nation",
        "member__user__profile__uploaded_picture",
        "member__user__bot",
        "member__rating_result",
    ).prefetch_related("member__nation_preferences__nation")
    hydrators = [
        PhaseStateMemberHydrator(),
    ]


class PhaseRetrieveLoader(Loader):
    queryset = Phase.objects.with_retrieve_data()
    hydrators = [
        ProvinceNationsHydrator(),
    ]
