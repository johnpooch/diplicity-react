from common.policies import Policy
from game.checks import IsGameMemberCheck, IsNotGameMemberCheck, IsNotSandboxGameCheck
from member.checks import HasUserCheck, IsNotOwnMemberCheck
from user_profile.checks import IsModeratorCheck

from .checks import (
    HasNotReportedCheck,
    IsAssignedInGameCheck,
    IsAssigneeCheck,
    IsPendingCheck,
    IsUnassignedCheck,
)


class CanReportPolicy(Policy):
    checks = [
        IsNotSandboxGameCheck,
        IsGameMemberCheck,
        HasUserCheck,
        IsNotOwnMemberCheck,
        HasNotReportedCheck,
    ]


class ModeratorPolicy(Policy):
    checks = [
        IsModeratorCheck,
    ]


class CanAssignPolicy(Policy):
    checks = [
        ModeratorPolicy,
        IsPendingCheck,
        IsUnassignedCheck,
        IsNotGameMemberCheck,
    ]


class CanUnassignPolicy(Policy):
    checks = [
        ModeratorPolicy,
        IsPendingCheck,
        IsAssigneeCheck,
    ]


class CanViewReportedGamePolicy(Policy):
    checks = [
        CanUnassignPolicy,
        IsNotGameMemberCheck,
    ]


class CanModerateGamePolicy(Policy):
    checks = [
        ModeratorPolicy,
        IsNotGameMemberCheck,
        IsAssignedInGameCheck,
    ]
