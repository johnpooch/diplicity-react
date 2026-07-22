from rest_framework import serializers
from django.apps import apps
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from .models import Channel, ChannelMessage, ChannelMember
from nation.serializers import NationSerializer
from member.serializers import BaseMemberSerializer
from emit import emit

Game = apps.get_model("game", "Game")
Member = apps.get_model("member", "Member")


class ChannelMemberSerializer(BaseMemberSerializer):
    nation = NationSerializer()


class ChannelMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    body = serializers.CharField(
        required=True,
        max_length=settings.CHAT_MESSAGE_MAX_CHARS,
        error_messages={
            "max_length": f"Messages cannot be longer than {settings.CHAT_MESSAGE_MAX_CHARS} characters."
        },
    )
    sender = ChannelMemberSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate(self, attrs):
        channel = self.context["channel"]
        member = self.context["current_game_member"]

        if channel.members.filter(user__bot_profile__isnull=False).exists():
            cap = settings.BOT_CHANNEL_MESSAGE_CAP
            message_count = channel.messages.filter(
                sender=member, phase=channel.game.current_phase
            ).count()
            if message_count >= cap:
                raise serializers.ValidationError(
                    f"You have reached the limit of {cap} messages for this channel this phase."
                )
        return attrs

    def create(self, validated_data):
        channel = self.context["channel"]
        member = self.context["current_game_member"]

        message = ChannelMessage.objects.create(
            channel=channel,
            sender=member,
            phase=channel.game.current_phase,
            body=validated_data["body"],
        )

        game = channel.game
        sender_name = "Anonymous" if game.anonymity_active else member.name
        emit(
            "channel_message",
            game=game,
            phase=game.current_phase or game.phases.last(),
            actor=member.user,
            channel=channel,
            context={"sender_name": sender_name, "body": message.body},
        )
        return message


class ChannelSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    private = serializers.BooleanField(read_only=True)
    messages = ChannelMessageSerializer(many=True, read_only=True)
    unread_message_count = serializers.IntegerField(read_only=True, default=0)
    message_limit = serializers.SerializerMethodField()
    member_message_count = serializers.SerializerMethodField()

    member_ids = serializers.ListField(child=serializers.IntegerField(), required=True, write_only=True)

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_message_limit(self, obj):
        if getattr(obj, "has_bot_member", False):
            return settings.BOT_CHANNEL_MESSAGE_CAP
        return None

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_member_message_count(self, obj):
        if getattr(obj, "has_bot_member", False):
            return getattr(obj, "member_message_count", 0)
        return None

    def validate_member_ids(self, value):
        game = self.context["game"]
        current_member = self.context["current_game_member"]

        member_ids = value + [current_member.id]
        channel_members = game.members.filter(id__in=member_ids)

        if channel_members.count() != len(member_ids):
            raise serializers.ValidationError("One or more members are not part of the game.")

        nations = sorted([m.nation.name for m in channel_members])
        channel_name = ", ".join(nations)

        if game.channels.filter(name=channel_name).exists():
            raise serializers.ValidationError("A channel with the same members already exists.")

        return value

    def create(self, validated_data):
        request = self.context["request"]
        game = self.context["game"]
        return Channel.objects.create_from_member_ids(request.user, validated_data["member_ids"], game)


class ChannelMarkReadSerializer(serializers.Serializer):
    def create(self, validated_data):
        channel = self.context["channel"]
        member = self.context["current_game_member"]
        channel_member = ChannelMember.objects.get(member=member, channel=channel)
        channel_member.last_read_at = timezone.now()
        channel_member.save(update_fields=["last_read_at"])
        return channel_member
