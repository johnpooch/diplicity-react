from rest_framework import serializers
from django.apps import apps
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from .models import Channel, ChannelMessage
from common.pagination import ChannelMessageCursorPagination
from nation.serializers import NationSerializer
from member.serializers import BaseMemberSerializer
from emit import emit

Game = apps.get_model("game", "Game")
Member = apps.get_model("member", "Member")


class ChannelMemberSerializer(BaseMemberSerializer):
    nation = NationSerializer(allow_null=True)


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

    def create(self, validated_data):
        channel = self.context["channel"]
        member = self.context["current_game_member"]

        message = ChannelMessage.objects.create(
            channel=channel,
            sender=member,
            phase=channel.game.current_phase,
            body=validated_data["body"],
        )

        emit("channel_message", message=message)
        return message


class ChannelPreviewSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    private = serializers.BooleanField(read_only=True)
    latest_message = serializers.SerializerMethodField()

    @extend_schema_field(ChannelMessageSerializer(allow_null=True))
    def get_latest_message(self, obj):
        latest_messages = getattr(obj, "latest_messages", [])
        if not latest_messages:
            return None
        return ChannelMessageSerializer(latest_messages[0], context=self.context).data


class ChannelCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    private = serializers.BooleanField(read_only=True)

    member_ids = serializers.ListField(child=serializers.IntegerField(), required=True, write_only=True)

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


class PaginatedChannelMessageListSerializer(serializers.Serializer):
    next = serializers.CharField(read_only=True, allow_null=True)
    previous = serializers.CharField(read_only=True, allow_null=True)
    results = ChannelMessageSerializer(many=True, read_only=True)


class ChannelRetrieveSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    private = serializers.BooleanField(read_only=True)
    messages = serializers.SerializerMethodField()

    @extend_schema_field(PaginatedChannelMessageListSerializer)
    def get_messages(self, obj):
        request = self.context["request"]
        paginator = ChannelMessageCursorPagination()
        page = paginator.paginate_queryset(obj.messages.with_sender_data(), request)
        return {
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": ChannelMessageSerializer(page, many=True, context=self.context).data,
        }


class ChannelMarkReadSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        instance.last_read_at = timezone.now()
        instance.save(update_fields=["last_read_at"])
        return instance


class ChannelUnreadSerializer(serializers.Serializer):
    total_unread_message_count = serializers.IntegerField(read_only=True)


class GameUnreadSerializer(serializers.Serializer):
    game_id = serializers.CharField(source="channel__game_id", read_only=True)
    total_unread_message_count = serializers.IntegerField(read_only=True)
