from common.loaders import Loader

from .hydrators import (
    CanCreateCommittedGameHydrator,
    CommitmentSquaresHydrator,
    MarksHydrator,
    PlayerStatsHydrator,
    ProfileRatingHydrator,
)
from .models import UserProfile


class UserProfileLoader(Loader):
    queryset = UserProfile.objects.with_related_data()
    hydrators = [
        CanCreateCommittedGameHydrator(),
    ]


class PublicUserProfileLoader(Loader):
    queryset = UserProfile.objects.with_related_data().with_commitment_total()
    hydrators = [
        CommitmentSquaresHydrator(),
        ProfileRatingHydrator(),
        MarksHydrator(),
        PlayerStatsHydrator(),
    ]
