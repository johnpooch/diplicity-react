from django.db import models
from django.db.models import Q, Count, Subquery, OuterRef, IntegerField, Value
from django.contrib.auth import get_user_model
from django.utils import timezone
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
            "messages", "messages__sender", "messages__sender__user", "members", "members__user"
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
                filter=Q(messages__created_at__gt=last_read_subquery),
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
        return self.select_related("sender", "sender__user")


class ChannelMessage(BaseModel):
    channel = models.ForeignKey("channel.Channel", on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField()

    objects = ChannelMessageQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
