from common.loaders import Loader

from .hydrators import (
    MemberActionsHydrator,
    MemberCommitmentHydrator,
    MemberVisibilityHydrator,
    NationPreferenceIdsHydrator,
    NationPreferencesHydrator,
    PieceCountsHydrator,
    ReportDecisionHydrator,
)
from .models import Member


class BaseMemberLoader(Loader):
    queryset = Member.objects.select_related(
        "game", "user__profile__uploaded_picture", "user__bot"
    )
    hydrators = [
        MemberVisibilityHydrator(),
    ]


class MemberLoader(Loader):
    queryset = Member.objects.select_related(
        "game",
        "nation",
        "user__profile__uploaded_picture",
        "user__bot",
        "rating_result",
    ).prefetch_related("nation_preferences__nation")
    hydrators = [
        MemberVisibilityHydrator(),
        MemberCommitmentHydrator(),
        NationPreferenceIdsHydrator(),
    ]


class MemberDetailLoader(Loader):
    queryset = Member.objects.with_detail_data()
    hydrators = [
        MemberVisibilityHydrator(),
        NationPreferencesHydrator(),
        MemberActionsHydrator(),
        ReportDecisionHydrator(),
        PieceCountsHydrator(),
    ]
