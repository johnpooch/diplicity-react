from common.policies import Policy
from game.checks import IsGameMemberCheck, IsNotGameMemberCheck, IsNotSandboxGameCheck
from member.checks import HasUserCheck, IsNotOwnMemberCheck
from user_profile.checks import IsModeratorCheck

from .checks import (
    HasNotReportedCheck,
    IsApprovedCheck,
    IsAssignedInGameCheck,
    IsAssigneeCheck,
    IsPendingCheck,
    IsUnassignedCheck,
    IsUnmarkedCheck,
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


class CanDecidePolicy(Policy):
    checks = [
        ModeratorPolicy,
        IsPendingCheck,
        IsAssigneeCheck,
        IsNotGameMemberCheck,
    ]


class MarkablePolicy(Policy):
    checks = [
        IsApprovedCheck,
        IsUnmarkedCheck,
    ]


class CanModerateGamePolicy(Policy):
    checks = [
        ModeratorPolicy,
        IsNotGameMemberCheck,
        IsAssignedInGameCheck,
    ]
