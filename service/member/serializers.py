from rest_framework import serializers
from django.apps import apps
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

    def _is_current_user(self, obj):
        if obj.user is None:
            return False
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user

    def _is_masked(self, obj):
        game = self._get_game(obj)
        if not game.anonymous:
            return False
        if game.status == GameStatus.COMPLETED:
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


class MemberSerializer(BaseMemberSerializer):
    nation = serializers.CharField(allow_null=True, read_only=True, source="nation.name")
    eliminated = serializers.BooleanField(read_only=True)
    kicked = serializers.BooleanField(read_only=True)
    is_game_master = serializers.SerializerMethodField()
    nmr_extensions_remaining = serializers.IntegerField(read_only=True)
    civil_disorder = serializers.BooleanField(read_only=True)
    confirmed = serializers.BooleanField(read_only=True)
    message = serializers.CharField(
        write_only=True, required=False, max_length=1000, allow_blank=False,
    )

    @extend_schema_field(serializers.BooleanField)
    def get_is_game_master(self, obj):
        if self._is_masked(obj):
            return False
        return obj.is_game_master

    def validate_message(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("Intro message cannot be blank.")
        return value.strip() if value else value

    def validate(self, attrs):
        game = self.context["game"]
        if game.press_type == PressType.FULL_PRESS and not attrs.get("message"):
            raise serializers.ValidationError(
                {"message": "An intro message is required when joining a full press game."}
            )
        return attrs

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user
        message_body = validated_data.pop("message", None)

        member = game.members.create(user=user)
        public_channels = game.channels.filter(private=False)
        ChannelMember.objects.bulk_create(
            [ChannelMember(member=member, channel=ch) for ch in public_channels]
        )

        if message_body:
            public_press = public_channels.filter(name="Public Press").first()
            if public_press:
                ChannelMessage.objects.create(
                    channel=public_press, sender=member, body=message_body,
                )

        return member
