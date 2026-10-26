from common.policies import Policy
from game.checks import IsCurrentPhaseActiveCheck
from game.policies import ActivePhasePlayerPolicy, ActivePlayerPolicy

from .checks import (
    HasNoActiveProposalCheck,
    HasNoPendingProposalCheck,
    HasNotVotedCheck,
    HasVoteCheck,
    IsAcceptedCheck,
    IsPendingCheck,
    IsProposerCheck,
)


class CanProposePolicy(Policy):
    checks = [
        ActivePhasePlayerPolicy,
        HasNoActiveProposalCheck,
        HasNoPendingProposalCheck,
    ]


class CanVotePolicy(Policy):
    checks = [
        ActivePhasePlayerPolicy,
        IsPendingCheck,
        HasVoteCheck,
        HasNotVotedCheck,
    ]


class CanCancelPolicy(Policy):
    checks = [
        ActivePlayerPolicy,
        IsProposerCheck,
        IsPendingCheck,
    ]


class ReadyToConcludePolicy(Policy):
    checks = [
        IsAcceptedCheck,
        IsCurrentPhaseActiveCheck,
    ]
