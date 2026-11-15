from common.loaders import Loader

from .hydrators import (
    GameMembersHydrator,
    ListPhasesHydrator,
    RetrievePhasesHydrator,
    TotalUnreadCountsHydrator,
    ViewerActionsHydrator,
    ViewerOrdersHydrator,
    ViewerPermissionsHydrator,
)
from .models import Game


class GameListLoader(Loader):
    queryset = Game.objects.with_list_data()
    hydrators = [
        ListPhasesHydrator(),
        TotalUnreadCountsHydrator(),
        GameMembersHydrator(),
        ViewerPermissionsHydrator(),
        ViewerOrdersHydrator(),
    ]


class GameRetrieveLoader(Loader):
    queryset = Game.objects.with_retrieve_data()
    hydrators = [
        RetrievePhasesHydrator(),
        GameMembersHydrator(),
        ViewerPermissionsHydrator(),
        ViewerOrdersHydrator(),
        ViewerActionsHydrator(),
    ]

    @classmethod
    def get_queryset(cls, actor):
        return super().get_queryset(actor).with_total_unread_counts(actor)
