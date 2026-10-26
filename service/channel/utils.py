import hashlib
import json

from django.db.models import Count, Max

from .models import Channel, ChannelEvent
from .policies import can_mute_channel, can_rename_channel
from .serializers import (
    ChannelEventSerializer,
    ChannelMemberSerializer,
    derive_channel_name,
)

CHANNEL_LIST_REPRESENTATION_VERSION = 3


def _digest(projection):
    canonical = json.dumps(projection, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


def channel_list_fingerprint(request, game, member):
    user = request.user
    accessible_as_member = member is not None
    channels = list(
        Channel.objects.accessible_to_member(member, game)
        .with_unread_counts(user)
        .with_mute_state(user)
        .with_member_names()
        .annotate(
            message_count=Count("messages", distinct=True),
            last_message_id=Max("messages__id"),
            last_message_created_at=Max("messages__created_at"),
            last_message_updated_at=Max("messages__updated_at"),
        )
        .order_by("id")
    )
    events = list(
        ChannelEvent.objects.for_display()
        .filter(channel__in=channels)
        .select_related("phase")
        .order_by("channel_id", "created_at", "id")
    )
    members = game.members.select_related(
        "user__profile__uploaded_picture", "nation__flag"
    ).order_by("id")
    context = {"request": request, "game": game}
    return _digest(
        [
            CHANNEL_LIST_REPRESENTATION_VERSION,
            [
                [
                    channel.id,
                    derive_channel_name(channel, context),
                    channel.title,
                    channel.private,
                    channel.created_at,
                    channel.unread_message_count,
                    channel.muted,
                    can_rename_channel(channel, game, member, accessible_as_member),
                    can_mute_channel(member, accessible_as_member),
                    channel.message_count,
                    channel.last_message_id,
                    channel.last_message_created_at,
                    channel.last_message_updated_at,
                ]
                for channel in channels
            ],
            list(
                zip(
                    [event.channel_id for event in events],
                    ChannelEventSerializer(events, many=True).data,
                )
            ),
            ChannelMemberSerializer(members, many=True, context=context).data,
        ]
    )
