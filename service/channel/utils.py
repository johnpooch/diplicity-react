import hashlib
import json

from django.db.models import Count, DateTimeField, Max, OuterRef, Subquery, Value

from .models import Channel, ChannelEvent, ChannelMember

CHANNEL_LIST_REPRESENTATION_VERSION = 1


def _requester_last_read_at(user):
    if not user.is_authenticated:
        return Value(None, output_field=DateTimeField())
    return Subquery(ChannelMember.objects.filter(channel=OuterRef("pk"), member__user=user).values("last_read_at")[:1])


def channel_list_fingerprint(request, game, member):
    user = request.user
    channels = list(
        Channel.objects.accessible_to_member(member, game)
        .with_unread_counts(user)
        .with_mute_state(user)
        .annotate(
            last_read_at=_requester_last_read_at(user),
            message_count=Count("messages", distinct=True),
            last_message_id=Max("messages__id"),
            last_message_created_at=Max("messages__created_at"),
            last_message_updated_at=Max("messages__updated_at"),
        )
        .order_by("id")
        .values_list(
            "id",
            "name",
            "title",
            "private",
            "created_at",
            "unread_message_count",
            "muted",
            "last_read_at",
            "message_count",
            "last_message_id",
            "last_message_created_at",
            "last_message_updated_at",
        )
    )
    channel_ids = [channel[0] for channel in channels]
    memberships = list(
        ChannelMember.objects.filter(channel_id__in=channel_ids)
        .order_by("channel_id", "member_id")
        .values_list("channel_id", "member_id")
    )
    events = list(
        ChannelEvent.objects.for_display()
        .filter(channel_id__in=channel_ids)
        .order_by("id")
        .values_list(
            "id",
            "channel_id",
            "type",
            "payload",
            "created_at",
            "updated_at",
            "phase__season",
            "phase__year",
            "phase__type",
        )
    )
    members = list(
        game.members.order_by("id").values_list(
            "id",
            "user_id",
            "kind",
            "user__profile__name",
            "user__profile__picture",
            "user__profile__commitment",
            "user__profile__kind",
            "user__profile__uploaded_picture__content_hash",
            "nation__nation_id",
            "nation__name",
            "nation__color",
            "nation__non_playable",
            "nation__variant_id",
            "nation__flag__content_hash",
        )
    )
    projection = [
        CHANNEL_LIST_REPRESENTATION_VERSION,
        request.build_absolute_uri("/"),
        user.id,
        [member.id, member.kind, member.kicked] if member else None,
        [game.id, game.anonymous, game.status, game.press_type, game.sandbox],
        channels,
        memberships,
        events,
        members,
    ]
    canonical = json.dumps(projection, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]
