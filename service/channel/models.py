from django.db import models
from django.db.models import Q, Count, F, OuterRef, Prefetch, Subquery
from django.contrib.auth import get_user_model
from django.utils import timezone
from channel import registry as channel_registry
from common.models import BaseModel

User = get_user_model()


class ChannelQuerySet(models.QuerySet):
    def accessible_to_user(self, user, game):
        queryset = self.filter(game=game)
        try:
            member = game.members.get(user=user)
            return queryset.filter(Q(private=False) | Q(members=member)).distinct()
        except:
            return queryset.filter(private=False)

    def with_preview_data(self):
        return self.annotate(
            latest_message_at=Subquery(
                ChannelMessage.objects.filter(channel=OuterRef("pk"))
                .order_by("-created_at")
                .values("created_at")[:1]
            )
        ).prefetch_related(
            Prefetch(
                "messages",
                queryset=ChannelMessage.objects.with_sender_data().order_by("-created_at")[:1],
                to_attr="latest_messages",
            )
        )

    def order_for_list(self):
        return self.order_by(
            "private",
            F("latest_message_at").desc(nulls_last=True),
            "-created_at",
        )


class ChannelManager(models.Manager):
    def get_queryset(self):
        return ChannelQuerySet(self.model, using=self._db)

    def create_from_member_ids(self, user, member_ids, game):
        member_ids = member_ids + [game.members.get(user=user).id]
        channel_members = game.members.filter(id__in=member_ids)
        nations = sorted([m.nation.name for m in channel_members])
        channel_name = ", ".join(nations)
        channel = self.create(name=channel_name, private=True, game=game)
        channel.members.set(channel_members)
        return channel

    def accessible_to_user(self, user, game):
        return self.get_queryset().accessible_to_user(user, game)

    def with_preview_data(self):
        return self.get_queryset().with_preview_data()

    def order_for_list(self):
        return self.get_queryset().order_for_list()


class Channel(BaseModel):

    objects = ChannelManager()

    name = models.CharField(max_length=1000)
    private = models.BooleanField(default=False)
    game = models.ForeignKey("game.Game", on_delete=models.CASCADE, related_name="channels")
    members = models.ManyToManyField(
        "member.Member",
        through="channel.ChannelMember",
        related_name="channels",
    )

    def member_user_ids(self):
        members = self.members if self.private else self.game.members
        return {m.user_id for m in members.all() if m.user_id is not None}


class ChannelMemberQuerySet(models.QuerySet):
    def unread_counts_by_channel(self, user):
        return (
            self.filter(member__user=user)
            .order_by()
            .values("channel_id")
            .annotate(
                unread_message_count=Count(
                    "channel__messages",
                    filter=Q(channel__messages__created_at__gt=F("last_read_at"))
                    & ~Q(channel__messages__sender__user=user),
                    distinct=True,
                )
            )
        )

    def unread_counts_by_game(self, user):
        return (
            self.filter(member__user=user)
            .order_by()
            .values("channel__game_id")
            .annotate(
                total_unread_message_count=Count(
                    "channel__messages",
                    filter=Q(channel__messages__created_at__gt=F("last_read_at"))
                    & ~Q(channel__messages__sender__user=user),
                    distinct=True,
                )
            )
        )


class ChannelMember(BaseModel):
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="member_channels")
    channel = models.ForeignKey("channel.Channel", on_delete=models.CASCADE, related_name="member_channels")
    last_read_at = models.DateTimeField(default=timezone.now)

    objects = ChannelMemberQuerySet.as_manager()

    class Meta:
        unique_together = ["member", "channel"]


class ChannelMessageQuerySet(models.QuerySet):
    def with_sender_data(self):
        return self.select_related(
            "sender__user__profile",
            "sender__nation",
            "sender__nation__flag",
        )


class ChannelMessage(BaseModel):
    channel = models.ForeignKey("channel.Channel", on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="sent_messages")
    phase = models.ForeignKey(
        "phase.Phase", on_delete=models.SET_NULL, null=True, blank=True, related_name="channel_messages"
    )
    body = models.TextField()

    objects = ChannelMessageQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["channel", "created_at"]),
        ]


class ChannelEventManager(models.Manager):
    def create_from_event(self, event_type, context):
        spec_class = channel_registry.REGISTRY.get(event_type)
        if spec_class is None:
            return []
        channels = spec_class().get_channels(context)
        if not channels:
            return []
        return self.create_for_channels(event_type, channels, phase=context.phase)

    def create_for_channels(self, event_type, channels, phase=None):
        return self.bulk_create(
            [self.model(channel=channel, type=event_type, phase=phase) for channel in channels]
        )


class ChannelEvent(BaseModel):
    channel = models.ForeignKey("channel.Channel", on_delete=models.CASCADE, related_name="events")
    phase = models.ForeignKey(
        "phase.Phase", on_delete=models.SET_NULL, null=True, blank=True, related_name="channel_events"
    )
    type = models.CharField(max_length=100)

    objects = ChannelEventManager()

    class Meta:
        ordering = ["created_at"]
