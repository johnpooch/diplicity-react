from django.db import models
from django.db.models import Q, Count, Subquery, OuterRef, IntegerField, Value, Max, F, Exists
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

    def for_game(self, game):
        return self.filter(game=game)

    def with_related_data(self):
        return self.prefetch_related(
            "messages", "messages__sender", "messages__sender__user", "messages__sender__user__bot_profile", "members", "members__user", "members__user__bot_profile"
        )

    def order_for_list(self):
        return self.annotate(last_activity=Max("messages__created_at")).order_by(
            "private",
            F("last_activity").desc(nulls_last=True),
            "-created_at",
        )

    def with_bot_membership(self):
        bot_members = ChannelMember.objects.filter(
            channel=OuterRef("pk"),
            member__user__bot_profile__isnull=False,
        )
        return self.annotate(has_bot_member=Exists(bot_members))

    def with_member_message_count(self, member, phase):
        if member is None or phase is None:
            return self.annotate(member_message_count=Value(0, output_field=IntegerField()))
        return self.annotate(
            member_message_count=Count(
                "messages",
                filter=Q(messages__sender=member) & Q(messages__phase=phase),
                distinct=True,
            )
        )

    def with_unread_counts(self, user):
        if not user.is_authenticated:
            return self.annotate(unread_message_count=Value(0, output_field=IntegerField()))
        last_read_subquery = Subquery(
            ChannelMember.objects.filter(
                channel=OuterRef("pk"),
                member__user=user,
            ).values("last_read_at")[:1]
        )
        return self.annotate(
            unread_message_count=Count(
                "messages",
                filter=Q(messages__created_at__gt=last_read_subquery)
                & ~Q(messages__sender__user=user),
                distinct=True,
            )
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

    def for_game(self, game):
        return self.get_queryset().for_game(game)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def with_unread_counts(self, user):
        return self.get_queryset().with_unread_counts(user)

    def with_bot_membership(self):
        return self.get_queryset().with_bot_membership()

    def with_member_message_count(self, member, phase):
        return self.get_queryset().with_member_message_count(member, phase)

    def order_for_list(self):
        return self.get_queryset().order_for_list()


class Channel(BaseModel):

    objects = ChannelManager()

    name = models.CharField(max_length=250)
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
    def for_channel(self, channel):
        return self.filter(channel=channel)


class ChannelMember(BaseModel):
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="member_channels")
    channel = models.ForeignKey("channel.Channel", on_delete=models.CASCADE, related_name="member_channels")
    last_read_at = models.DateTimeField(default=timezone.now)

    objects = ChannelMemberQuerySet.as_manager()

    class Meta:
        unique_together = ["member", "channel"]


class ChannelMessageQuerySet(models.QuerySet):
    def for_channel(self, channel):
        return self.filter(channel=channel)

    def with_sender_data(self):
        return self.select_related("sender", "sender__user", "sender__user__bot_profile")


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
