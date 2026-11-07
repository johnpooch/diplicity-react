import hashlib
import json

from django.apps import apps
from django.db import IntegrityError, models, transaction
from django.http import Http404
from django.db.models import (
    Q,
    BooleanField,
    Case,
    Count,
    Exists,
    Subquery,
    OuterRef,
    IntegerField,
    Value,
    Max,
    F,
    When,
)
from django.contrib.auth import get_user_model
from django.core import exceptions
from django.utils import timezone
from channel import registry as channel_registry
from common.models import BaseModel
from emit import emit

User = get_user_model()

CHANNEL_TITLE_MAX_LENGTH = 50
CHANNEL_DETAIL_REPRESENTATION_VERSION = 1


class ChannelQuerySet(models.QuerySet):
    def accessible_to_member(self, member, game):
        queryset = self.filter(game=game)
        if member is None:
            return queryset.filter(private=False)
        return queryset.filter(Q(private=False) | Q(members=member)).distinct()

    def accessible_to_user(self, user, game):
        try:
            member = game.members.get(user=user)
        except:
            member = None
        return self.accessible_to_member(member, game)

    def for_game(self, game):
        return self.filter(game=game)

    def with_member_names(self):
        return self.prefetch_related("members__nation", "members__user__profile")

    def with_latest_message_id(self):
        latest_message = (
            ChannelMessage.objects.filter(channel=OuterRef("pk"))
            .order_by("-created_at", "-id")
            .values("id")[:1]
        )
        return self.annotate(latest_message_id=Subquery(latest_message))

    def with_first_unread_message_id(self, user):
        if not user.is_authenticated:
            return self.annotate(
                first_unread_message_id=Value(None, output_field=IntegerField())
            )
        first_unread_message = (
            ChannelMessage.objects.filter(channel=OuterRef("pk"))
            .unread_by(user)
            .order_by("created_at", "id")
            .values("id")[:1]
        )
        return self.annotate(first_unread_message_id=Subquery(first_unread_message))

    def with_requester_membership(self, member):
        if member is None:
            return self.annotate(
                requester_is_member=Value(False, output_field=BooleanField())
            )
        membership = ChannelMember.objects.filter(channel=OuterRef("pk"), member=member)
        return self.annotate(
            requester_is_member=Case(
                When(private=False, then=Value(True)),
                default=Exists(membership),
                output_field=BooleanField(),
            )
        )

    def with_latest_event_id(self):
        latest_event = (
            ChannelEvent.objects.for_display()
            .filter(channel=OuterRef("pk"))
            .order_by("-created_at", "-id")
            .values("id")[:1]
        )
        return self.annotate(latest_event_id=Subquery(latest_event))

    def with_detail_data(self):
        return self.with_latest_event_id().prefetch_related(
            models.Prefetch(
                "events",
                queryset=ChannelEvent.objects.for_display().select_related("phase"),
            )
        )

    def order_for_list(self):
        return self.annotate(last_activity=Max("messages__created_at")).order_by(
            "private",
            F("last_activity").desc(nulls_last=True),
            "-created_at",
        )

    def with_unread_counts(self, user):
        if not user.is_authenticated:
            return self.annotate(
                unread_message_count=Value(0, output_field=IntegerField())
            )
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

    def with_mute_state(self, user):
        if not user.is_authenticated:
            return self.annotate(muted=Value(False, output_field=BooleanField()))
        active_mute = ChannelMember.objects.filter(
            channel=OuterRef("pk"),
            member__user=user,
        ).filter(Q(muted_indefinitely=True) | Q(muted_until__gt=timezone.now()))
        return self.annotate(muted=Exists(active_mute))


class ChannelManager(models.Manager):

    def create(self, **kwargs):
        channel = super().create(**kwargs)
        apps.get_model("game", "Game").objects.bump_version([channel.game_id])
        return channel

    def save_channel(self, channel, **kwargs):
        channel.save(**kwargs)
        apps.get_model("game", "Game").objects.bump_version([channel.game_id])
        return channel

    def delete_channels(self, channels):
        game_ids = tuple(channels.values_list("game_id", flat=True))
        result = channels.delete()
        apps.get_model("game", "Game").objects.bump_version(game_ids)
        return result

    @transaction.atomic
    def rename(self, channel, title, actor_name):
        if title == channel.title:
            return channel
        channel.title = title
        self.save_channel(channel, update_fields=["title"])
        emit(
            "channel_renamed",
            game=channel.game,
            phase=channel.game.current_phase,
            channel=channel,
            nation=actor_name,
            name=title,
        )
        return channel

    @transaction.atomic
    def leave(self, channel, member, actor_name):
        ChannelMember.objects.delete_memberships(
            ChannelMember.objects.filter(member=member, channel=channel)
        )
        emit(
            "channel_left",
            game=channel.game,
            phase=channel.game.current_phase,
            channel=channel,
            nation=actor_name,
        )
        return channel

    def retrieve_fingerprint(self, game_id, channel_id, request):
        user = request.user
        member = apps.get_model("member", "Member").objects.filter(
            game_id=OuterRef("game_id"), user_id=user.id
        )
        membership = ChannelMember.objects.filter(
            channel_id=OuterRef("pk"), member__user_id=user.id
        )
        if not user.is_authenticated:
            member = member.none()
            membership = membership.none()
        report = apps.get_model("report", "Report").objects.filter(
            reported__game_id=OuterRef("game_id"),
            reported__left_at__isnull=True,
            assigned_to_id=user.id,
            review__isnull=True,
        )
        moderator = apps.get_model("user_profile", "UserProfile").objects.filter(
            user_id=user.id, is_moderator=True
        )
        message = ChannelMessage.objects.filter(channel_id=OuterRef("pk")).order_by(
            "-id"
        )
        channel = (
            self.filter(pk=channel_id, game_id=game_id)
            .annotate(
                requester_is_member=Exists(member),
                requester_is_channel_member=Exists(
                    membership.filter(member__left_at__isnull=True)
                ),
                requester_is_moderator=Exists(moderator),
                requester_has_report=Exists(report),
                last_read_at=Subquery(membership.values("last_read_at")[:1]),
                latest_message_id=Subquery(message.values("id")[:1]),
            )
            .filter(
                Q(private=False)
                | Q(requester_is_channel_member=True)
                | Q(
                    requester_is_member=False,
                    requester_is_moderator=True,
                    requester_has_report=True,
                )
            )
            .with_mute_state(user)
            .with_latest_event_id()
            .values(
                "game__version",
                "name",
                "title",
                "private",
                "last_read_at",
                "muted",
                "latest_message_id",
                "latest_event_id",
                "requester_is_member",
                "requester_is_moderator",
                "requester_has_report",
            )
            .first()
        )
        if channel is None:
            raise Http404
        canonical = json.dumps(
            [
                CHANNEL_DETAIL_REPRESENTATION_VERSION,
                user.id,
                request.build_absolute_uri("/"),
                channel,
            ],
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]

    def get_queryset(self):
        return ChannelQuerySet(self.model, using=self._db)

    @transaction.atomic
    def create_from_member_ids(self, user, member_ids, game, title=""):
        member_ids = member_ids + [game.members.players().get(user=user).id]
        channel_members = game.members.players().filter(id__in=member_ids)
        channel = self.create(title=title, private=True, game=game)
        channel.members.set(channel_members)
        apps.get_model("game", "Game").objects.bump_version([game.pk])
        return channel

    def private_channel_exists_for_members(self, game, member_ids):
        return any(
            {
                member.id
                for member in channel.members.all()
                if member.replaced_by_id is None
            }
            == set(member_ids)
            for channel in self.filter(game=game, private=True).prefetch_related(
                "members"
            )
        )

    def accessible_to_user(self, user, game):
        return self.get_queryset().accessible_to_user(user, game)

    def accessible_to_member(self, member, game):
        return self.get_queryset().accessible_to_member(member, game)

    def for_game(self, game):
        return self.get_queryset().for_game(game)

    def with_unread_counts(self, user):
        return self.get_queryset().with_unread_counts(user)

    def with_mute_state(self, user):
        return self.get_queryset().with_mute_state(user)

    def order_for_list(self):
        return self.get_queryset().order_for_list()

    def hydrate_latest_messages(self, channels):
        messages = ChannelMessage.objects.with_sender_data().in_bulk(
            [
                channel.latest_message_id
                for channel in channels
                if channel.latest_message_id is not None
            ]
        )
        for channel in channels:
            channel.latest_message = messages.get(channel.latest_message_id)


class Channel(BaseModel):

    objects = ChannelManager()

    name = models.CharField(max_length=1000)
    title = models.CharField(
        max_length=CHANNEL_TITLE_MAX_LENGTH, blank=True, default=""
    )
    private = models.BooleanField(default=False)
    game = models.ForeignKey(
        "game.Game", on_delete=models.CASCADE, related_name="channels"
    )
    members = models.ManyToManyField(
        "member.Member",
        through="channel.ChannelMember",
        related_name="channels",
    )

    def member_user_ids(self):
        members = self.members if self.private else self.game.members
        return {
            m.user_id for m in members.all() if m.user_id is not None and m.occupied
        }

    def notifiable_member_user_ids(self):
        muted_user_ids = set(
            self.member_channels.filter(
                Q(muted_indefinitely=True) | Q(muted_until__gt=timezone.now())
            ).values_list("member__user_id", flat=True)
        )
        return self.member_user_ids() - muted_user_ids


class ChannelMemberQuerySet(models.QuerySet):
    def for_channel(self, channel):
        return self.filter(channel=channel)


class ChannelMemberManager(models.Manager.from_queryset(ChannelMemberQuerySet)):
    def create(self, **kwargs):
        membership = super().create(**kwargs)
        apps.get_model("game", "Game").objects.bump_version(
            [membership.channel.game_id]
        )
        return membership

    def save_membership(self, membership):
        membership.save()
        apps.get_model("game", "Game").objects.bump_version(
            [membership.channel.game_id]
        )

    def delete_memberships(self, memberships):
        game_ids = tuple(memberships.values_list("channel__game_id", flat=True))
        result = memberships.delete()
        apps.get_model("game", "Game").objects.bump_version(game_ids)
        return result


class ChannelMember(BaseModel):
    member = models.ForeignKey(
        "member.Member", on_delete=models.CASCADE, related_name="member_channels"
    )
    channel = models.ForeignKey(
        "channel.Channel", on_delete=models.CASCADE, related_name="member_channels"
    )
    last_read_at = models.DateTimeField(default=timezone.now)
    muted_until = models.DateTimeField(null=True, blank=True)
    muted_indefinitely = models.BooleanField(default=False)

    objects = ChannelMemberManager()

    class Meta:
        unique_together = ["member", "channel"]

    @property
    def muted(self):
        return self.muted_indefinitely or (
            self.muted_until is not None and self.muted_until > timezone.now()
        )


class ChannelMessageQuerySet(models.QuerySet):

    def save_message(self, message):
        message.save()
        apps.get_model("game", "Game").objects.bump_version([message.channel.game_id])

    def delete_messages(self):
        game_ids = tuple(self.values_list("channel__game_id", flat=True))
        result = self.delete()
        apps.get_model("game", "Game").objects.bump_version(game_ids)
        return result

    def for_channel(self, channel):
        return self.filter(channel=channel)

    def with_sender_data(self):
        return self.select_related(
            "sender",
            "sender__user",
            "sender__user__profile__uploaded_picture",
            "sender__nation__flag",
        )

    def page(self, *, page_size, before=None, after=None):
        if after is not None:
            window = list(self.filter(id__gt=after).order_by("id")[: page_size + 1])
            has_older = self.filter(id__lte=after).exists()
            has_newer = len(window) > page_size
        else:
            older = self if before is None else self.filter(id__lt=before)
            window = list(older.order_by("-id")[: page_size + 1])
            has_older = len(window) > page_size
            has_newer = before is not None and self.filter(id__gte=before).exists()
        return {
            "results": sorted(
                window[:page_size], key=lambda message: (message.created_at, message.id)
            ),
            "has_older": has_older,
            "has_newer": has_newer,
        }

    def unread_by(self, user):
        last_read_subquery = Subquery(
            ChannelMember.objects.filter(
                channel=OuterRef("channel"),
                member__user=user,
            ).values("last_read_at")[:1]
        )
        return self.filter(
            channel__member_channels__member__user=user,
            created_at__gt=last_read_subquery,
        ).exclude(sender__user=user)

    def create_idempotent(self, channel, sender, phase, body, client_message_id):
        if client_message_id is None:
            return (
                self.create(channel=channel, sender=sender, phase=phase, body=body),
                True,
            )
        try:
            with transaction.atomic():
                message = self.create(
                    channel=channel,
                    sender=sender,
                    phase=phase,
                    body=body,
                    client_message_id=client_message_id,
                )
        except IntegrityError:
            message = self.filter(
                channel=channel,
                sender=sender,
                client_message_id=client_message_id,
                body=body,
            ).first()
            if message is None:
                raise exceptions.ValidationError(
                    "This client message id has already been used for another message."
                )
            return message, False
        return message, True


class ChannelMessage(BaseModel):
    channel = models.ForeignKey(
        "channel.Channel", on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        "member.Member", on_delete=models.CASCADE, related_name="sent_messages"
    )
    phase = models.ForeignKey(
        "phase.Phase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="channel_messages",
    )
    body = models.TextField()
    client_message_id = models.UUIDField(null=True, blank=True)

    objects = ChannelMessageQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "client_message_id"],
                condition=Q(client_message_id__isnull=False),
                name="channel_message_unique_client_id_per_sender",
            ),
        ]


class ChannelEventQuerySet(models.QuerySet):
    def for_display(self):
        return self.filter(type__in=channel_registry.displayed_event_types())


class ChannelEventManager(models.Manager):
    def get_queryset(self):
        return ChannelEventQuerySet(self.model, using=self._db)

    def for_display(self):
        return self.get_queryset().for_display()

    def create_from_event(self, event_type, context):
        spec_class = channel_registry.REGISTRY.get(event_type)
        if spec_class is None:
            return []
        channels = spec_class().get_channels(context)
        if not channels:
            return []
        return self.create_for_channels(
            event_type,
            channels,
            phase=context.phase,
            payload=spec_class().build_payload(context),
        )

    def create_for_channels(self, event_type, channels, phase=None, payload=None):
        return self.bulk_create(
            [
                self.model(
                    channel=channel, type=event_type, phase=phase, payload=payload or {}
                )
                for channel in channels
            ]
        )


class ChannelEvent(BaseModel):
    channel = models.ForeignKey(
        "channel.Channel", on_delete=models.CASCADE, related_name="events"
    )
    phase = models.ForeignKey(
        "phase.Phase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="channel_events",
    )
    type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict, blank=True)

    objects = ChannelEventManager()

    class Meta:
        ordering = ["created_at"]

    @property
    def text(self):
        spec_class = channel_registry.REGISTRY.get(self.type)
        if spec_class is None:
            return None
        return spec_class().render(self)
