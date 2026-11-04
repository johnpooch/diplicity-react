from common.policies import Policy
from game.checks import (
    IsCompletedGameCheck,
    IsPublicGameCheck,
    IsRankedGameCheck,
)

from .checks import HasPlayedMinimumYearsCheck, IsRankedVariantCheck, IsUnratedCheck


class RankablePolicy(Policy):
    checks = [
        IsPublicGameCheck,
        IsRankedVariantCheck,
    ]


class RateablePolicy(Policy):
    checks = [
        IsRankedGameCheck,
        IsCompletedGameCheck,
        HasPlayedMinimumYearsCheck,
        IsUnratedCheck,
    ]
