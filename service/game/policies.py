from common.policies import Policy

from .checks import (
    IsActiveGameCheck,
    IsActivePlayerCheck,
    IsCurrentPhaseActiveCheck,
    IsGamePlayerCheck,
    IsNotSandboxGameCheck,
)


class ActivePlayerPolicy(Policy):
    checks = [
        IsActiveGameCheck,
        IsGamePlayerCheck,
        IsActivePlayerCheck,
        IsNotSandboxGameCheck,
    ]


class ActivePhasePlayerPolicy(Policy):
    checks = [
        ActivePlayerPolicy,
        IsCurrentPhaseActiveCheck,
    ]
