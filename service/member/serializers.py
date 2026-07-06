from rest_framework import serializers
from django.apps import apps
from django.conf import settings
from django.db import transaction
from drf_spectacular.utils import extend_schema_field

from common.constants import GameStatus, PressType

ChannelMember = apps.get_model("channel", "ChannelMember")
ChannelMessage = apps.get_model("channel", "ChannelMessage")


class BaseMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    is_current_user = serializers.SerializerMethodField()
    is_bot = serializers.SerializerMethodField()

    def _is_current_user(self, obj):
        if obj.user is None:
            return False
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user

    def _is_bot(self, obj):
        return obj.user is not None and hasattr(obj.user, "bot_profile")

    def _is_masked(self, obj):
        game = self._get_game(obj)
        if not game.anonymous:
            return False
        if game.status == GameStatus.COMPLETED:
            return False
        if self._is_bot(obj):
            return False
        return not self._is_current_user(obj)

    def _get_game(self, obj):
        if "game" in self.context:
            return self.context["game"]
        return obj.game

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_user_id(self, obj):
        if self._is_masked(obj):
            return None
        if obj.user is None:
            return None
        return obj.user_id

    @extend_schema_field(serializers.CharField)
    def get_name(self, obj):
        if self._is_masked(obj):
            return "Anonymous"
        if obj.user is None:
            return "Deleted User"
        return obj.user.profile.name

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_picture(self, obj):
        if self._is_masked(obj):
            return None
        if obj.user is None:
            return None
        return obj.user.profile.picture

    @extend_schema_field(serializers.BooleanField)
    def get_is_current_user(self, obj):
        return self._is_current_user(obj)

    @extend_schema_field(serializers.BooleanField)
    def get_is_bot(self, obj):
        return self._is_bot(obj)


class MemberSerializer(BaseMemberSerializer):
    nation = serializers.CharField(allow_null=True, read_only=True, source="nation.name")
    eliminated = serializers.BooleanField(read_only=True)
    kicked = serializers.BooleanField(read_only=True)
    is_game_creator = serializers.SerializerMethodField()
    nmr_extensions_remaining = serializers.IntegerField(read_only=True)
    civil_disorder = serializers.BooleanField(read_only=True)
    seeking_replacement = serializers.BooleanField(read_only=True)
    replaceable = serializers.BooleanField(read_only=True)
    intro_message = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        max_length=settings.CHAT_MESSAGE_MAX_CHARS,
        error_messages={
            "max_length": f"Messages cannot be longer than {settings.CHAT_MESSAGE_MAX_CHARS} characters."
        },
    )

    @extend_schema_field(serializers.BooleanField)
    def get_is_game_creator(self, obj):
        if self._is_masked(obj):
            return False
        game = self._get_game(obj)
        return obj.user_id is not None and obj.user_id == game.created_by_id

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user

        with transaction.atomic():
            member = game.members.create(user=user)
            public_channels = list(game.channels.filter(private=False))
            ChannelMember.objects.bulk_create(
                [ChannelMember(member=member, channel=ch) for ch in public_channels]
            )

            intro_message = validated_data.get("intro_message")
            public_channel = public_channels[0] if public_channels else None
            if intro_message and public_channel is not None and game.press_type != PressType.NO_PRESS and not game.anonymous:
                ChannelMessage.objects.create(
                    channel=public_channel,
                    sender=member,
                    phase=game.current_phase,
                    body=intro_message,
                )

        return member
