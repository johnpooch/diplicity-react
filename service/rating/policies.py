from common.policies import Policy
from game.checks import IsCompletedGameCheck, IsRankedGameCheck

from .checks import HasPlayedMinimumYearsCheck, IsUnratedCheck


class RateablePolicy(Policy):
    checks = [
        IsRankedGameCheck,
        IsCompletedGameCheck,
        HasPlayedMinimumYearsCheck,
        IsUnratedCheck,
    ]
