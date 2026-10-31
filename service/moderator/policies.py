from common.policies import Policy

from .checks import IsModeratorCheck


class ModeratorPolicy(Policy):
    checks = [
        IsModeratorCheck,
    ]
