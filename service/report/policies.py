from common.policies import Policy
from game.checks import IsGameMemberCheck, IsNotSandboxGameCheck
from member.checks import HasUserCheck, IsNotOwnMemberCheck
from user_profile.checks import IsModeratorCheck

from .checks import HasNotReportedCheck


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
