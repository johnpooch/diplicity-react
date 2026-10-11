import hashlib
import json

from django.db.models import Count, Max

from .models import Channel, ChannelEvent, ChannelMessage
from .policies import can_mute_channel, can_rename_channel
from .serializers import ChannelEventSerializer, ChannelMemberSerializer, ChannelMessageSerializer

CHANNEL_LIST_REPRESENTATION_VERSION = 2
CHANNEL_PREVIEW_REPRESENTATION_VERSION = 1
CHANNEL_DETAIL_REPRESENTATION_VERSION = 1


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
    members = game.members.select_related("user__profile__uploaded_picture", "nation__flag").order_by("id")
    context = {"request": request, "game": game}
    return _digest(
        [
            CHANNEL_LIST_REPRESENTATION_VERSION,
            [
                [
                    channel.id,
                    channel.name,
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
            list(zip([event.channel_id for event in events], ChannelEventSerializer(events, many=True).data)),
            ChannelMemberSerializer(members, many=True, context=context).data,
        ]
    )


def channel_preview_fingerprint(request, game, member):
    user = request.user
    channels = list(
        Channel.objects.accessible_to_member(member, game)
        .with_unread_counts(user)
        .with_mute_state(user)
        .with_latest_message_id()
        .order_by("id")
    )
    latest_messages = (
        ChannelMessage.objects.filter(
            id__in=[channel.latest_message_id for channel in channels if channel.latest_message_id is not None]
        )
        .with_sender_data()
        .select_related("sender__nation__flag")
        .order_by("id")
    )
    context = {"request": request, "game": game}
    return _digest(
        [
            CHANNEL_PREVIEW_REPRESENTATION_VERSION,
            [
                [
                    channel.id,
                    channel.name,
                    channel.title,
                    channel.private,
                    channel.created_at,
                    channel.unread_message_count,
                    channel.muted,
                    channel.latest_message_id,
                ]
                for channel in channels
            ],
            ChannelMessageSerializer(latest_messages, many=True, context=context).data,
        ]
    )


def channel_detail_fingerprint(channel, game, member):
    accessible_as_member = member is not None
    return _digest(
        [
            CHANNEL_DETAIL_REPRESENTATION_VERSION,
            channel.id,
            channel.name,
            channel.title,
            channel.private,
            channel.unread_message_count,
            channel.muted,
            can_rename_channel(channel, game, member, accessible_as_member),
            can_mute_channel(member, accessible_as_member),
            channel.first_unread_message_id,
            channel.latest_message_id,
            channel.latest_event_id,
            ChannelEventSerializer(channel.events.all(), many=True).data,
        ]
    )
