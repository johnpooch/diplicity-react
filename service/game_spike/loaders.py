from common.loaders import Loader

from .hydrators import CommitmentTotals, CurrentBoard, LatestPhaseStates, PendingDrawVotes, UnreadCounts
from .query import game_queryset


class GameRetrieveLoader(Loader):
    queryset = game_queryset
    hydrators = [LatestPhaseStates, UnreadCounts, CommitmentTotals]


class GameListLoader(Loader):
    queryset = game_queryset
    hydrators = [LatestPhaseStates, CurrentBoard, UnreadCounts, CommitmentTotals]


class MyGameLoader(Loader):
    queryset = game_queryset
    hydrators = [LatestPhaseStates, CurrentBoard, UnreadCounts, PendingDrawVotes]
