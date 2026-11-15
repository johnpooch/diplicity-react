from common.loaders import Loader

from .hydrators import ChannelPermissionsHydrator
from .models import Channel


class ChannelLoader(Loader):
    queryset = Channel.objects.select_related("game").with_member_names()
    hydrators = [
        ChannelPermissionsHydrator(),
    ]


class ChannelDetailLoader(Loader):
    queryset = (
        Channel.objects.select_related("game")
        .with_latest_message_id()
        .with_detail_data()
        .with_member_names()
    )
    hydrators = [
        ChannelPermissionsHydrator(),
    ]

    @classmethod
    def get_queryset(cls, actor):
        return (
            super()
            .get_queryset(actor)
            .with_unread_counts(actor)
            .with_mute_state(actor)
            .with_first_unread_message_id(actor)
        )
