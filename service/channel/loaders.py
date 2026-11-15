from common.loaders import Loader

from .hydrators import (
    ChannelNameHydrator,
    ChannelPermissionsHydrator,
    LatestMessageHydrator,
    SenderHydrator,
)
from .models import Channel, ChannelMessage


class ChannelMessageLoader(Loader):
    queryset = ChannelMessage.objects.with_sender_data()
    hydrators = [
        SenderHydrator(),
    ]


class ChannelLoader(Loader):
    queryset = Channel.objects.select_related("game").with_member_names()
    hydrators = [
        ChannelNameHydrator(),
        ChannelPermissionsHydrator(),
    ]
    nested = {"messages": ChannelMessageLoader}


class ChannelPreviewLoader(Loader):
    queryset = Channel.objects.all().with_latest_message_id().with_member_names()
    hydrators = [
        ChannelNameHydrator(),
        LatestMessageHydrator(),
    ]

    @classmethod
    def get_queryset(cls, actor):
        return super().get_queryset(actor).with_unread_counts(actor).with_mute_state(actor)


class ChannelDetailLoader(Loader):
    queryset = (
        Channel.objects.select_related("game")
        .with_latest_message_id()
        .with_detail_data()
        .with_member_names()
    )
    hydrators = [
        ChannelNameHydrator(),
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
