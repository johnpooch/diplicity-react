from common.policies import Policy
from game.checks import IsGameMemberCheck, IsNotSandboxGameCheck

from .checks import HasNotReportedCheck, HasUserCheck, IsNotOwnMemberCheck


class CanReportPolicy(Policy):
    checks = [
        IsNotSandboxGameCheck,
        IsGameMemberCheck,
        HasUserCheck,
        IsNotOwnMemberCheck,
        HasNotReportedCheck,
    ]
