from datetime import timedelta

from rest_framework import serializers
from django.apps import apps
from django.conf import settings
from django.core import exceptions
from django.utils import timezone

from .models import Channel, ChannelMessage, ChannelMember, CHANNEL_TITLE_MAX_LENGTH
from .policies import can_mute_channel, can_rename_channel
from nation.serializers import NationSerializer
from member.serializers import BaseMemberSerializer
from emit import emit

Game = apps.get_model("game", "Game")
Member = apps.get_model("member", "Member")


class ChannelMemberSerializer(BaseMemberSerializer):
    nation = NationSerializer(allow_null=True)
    is_game_master = serializers.BooleanField(read_only=True)


class ChannelMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    body = serializers.CharField(
        required=True,
        max_length=settings.CHAT_MESSAGE_MAX_CHARS,
        error_messages={
            "max_length": f"Messages cannot be longer than {settings.CHAT_MESSAGE_MAX_CHARS} characters."
        },
    )
    client_message_id = serializers.UUIDField(required=False, allow_null=True)
    sender = ChannelMemberSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        channel = self.context["channel"]
        member = self.context["current_game_member"]

        try:
            message, created = ChannelMessage.objects.create_idempotent(
                channel=channel,
                sender=member,
                phase=channel.game.current_phase,
                body=validated_data["body"],
                client_message_id=validated_data.get("client_message_id"),
            )
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"client_message_id": e.messages})

        if created:
            emit("channel_message", message=message)
        return message


class ChannelEventSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    text = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ChannelSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    title = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=CHANNEL_TITLE_MAX_LENGTH,
        error_messages={
            "max_length": f"Channel names cannot be longer than {CHANNEL_TITLE_MAX_LENGTH} characters."
        },
    )
    private = serializers.BooleanField(read_only=True)
    messages = ChannelMessageSerializer(many=True, read_only=True)
    events = ChannelEventSerializer(many=True, read_only=True)
    unread_message_count = serializers.IntegerField(read_only=True, default=0)
    muted = serializers.BooleanField(read_only=True, default=False)
    can_rename = serializers.SerializerMethodField()
    can_mute = serializers.SerializerMethodField()

    member_ids = serializers.ListField(child=serializers.IntegerField(), required=True, write_only=True)

    def is_channel_member(self, channel, member):
        if member is None:
            return False
        if not channel.private:
            return True
        return any(channel_member.id == member.id for channel_member in channel.members.all())

    def get_can_rename(self, channel) -> bool:
        game = self.context["game"]
        member = self.context.get("current_game_member")
        return can_rename_channel(
            channel,
            game,
            member,
            self.is_channel_member(channel, member),
        )

    def get_can_mute(self, channel) -> bool:
        member = self.context.get("current_game_member")
        return can_mute_channel(member, self.is_channel_member(channel, member))

    def validate_member_ids(self, value):
        game = self.context["game"]
        current_member = self.context["current_game_member"]

        member_ids = value + [current_member.id]
        channel_members = game.members.players().filter(id__in=member_ids)

        if channel_members.count() != len(member_ids):
            raise serializers.ValidationError("One or more members are not part of the game.")

        nations = sorted([m.nation.name for m in channel_members])
        channel_name = ", ".join(nations)

        if game.channels.filter(name=channel_name).exists():
            raise serializers.ValidationError("Channel already exists.")

        return value

    def create(self, validated_data):
        request = self.context["request"]
        game = self.context["game"]
        return Channel.objects.create_from_member_ids(
            request.user, validated_data["member_ids"], game, validated_data.get("title", "")
        )


class ChannelUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=CHANNEL_TITLE_MAX_LENGTH,
        error_messages={
            "max_length": f"Channel names cannot be longer than {CHANNEL_TITLE_MAX_LENGTH} characters."
        },
    )

    def update(self, instance, validated_data):
        title = validated_data["title"]
        if title == instance.title:
            return instance

        member = self.context["current_game_member"]
        instance.title = title
        instance.save(update_fields=["title"])

        emit(
            "channel_renamed",
            game=instance.game,
            phase=instance.game.current_phase,
            channel=instance,
            nation=member.nation.name,
            name=title,
        )
        return instance


class ChannelMarkReadSerializer(serializers.Serializer):
    def create(self, validated_data):
        channel = self.context["channel"]
        member = self.context["current_game_member"]
        channel_member = ChannelMember.objects.get(member=member, channel=channel)
        channel_member.last_read_at = timezone.now()
        channel_member.save(update_fields=["last_read_at"])
        return channel_member


class ChannelMuteSerializer(serializers.Serializer):
    muted = serializers.BooleanField(read_only=True)
    mute_duration = serializers.ChoiceField(
        choices=("8_hours", "24_hours", "indefinite"),
        allow_null=True,
        required=True,
        write_only=True,
    )

    def validate(self, attrs):
        if "mute_duration" not in attrs:
            raise serializers.ValidationError(
                {"mute_duration": "This field is required."}
            )
        return attrs

    def update(self, instance, validated_data):
        duration = validated_data["mute_duration"]
        instance.muted_until = None
        instance.muted_indefinitely = duration == "indefinite"
        if duration == "8_hours":
            instance.muted_until = timezone.now() + timedelta(hours=8)
        elif duration == "24_hours":
            instance.muted_until = timezone.now() + timedelta(hours=24)
        instance.save(update_fields=["muted_until", "muted_indefinitely"])
        return instance
