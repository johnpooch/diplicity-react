from rest_framework import serializers
from django.apps import apps
from drf_spectacular.utils import extend_schema_field

from bot.models import BotProfile
from member.serializers import MemberSerializer

ChannelMember = apps.get_model("channel", "ChannelMember")


class AvailableBotSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(source="user.profile.name", read_only=True)
    picture = serializers.CharField(source="user.profile.picture", read_only=True, allow_null=True)


class BotMemberCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(write_only=True)

    def validate_user_id(self, value):
        game = self.context["game"]
        bot_profile = (
            BotProfile.objects.available_for_game(game).filter(user_id=value).first()
        )
        if bot_profile is None:
            raise serializers.ValidationError(
                "This bot is not available to add to this game."
            )
        self._bot_user = bot_profile.user
        return value

    def create(self, validated_data):
        game = self.context["game"]
        member = game.members.create(user=self._bot_user)
        public_channels = game.channels.filter(private=False)
        ChannelMember.objects.bulk_create(
            [ChannelMember(member=member, channel=ch) for ch in public_channels]
        )
        return member

    def to_representation(self, instance):
        return MemberSerializer(instance, context=self.context).data


class LLMCallSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    stage = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    model = serializers.CharField(read_only=True)
    game_id = serializers.CharField(source="phase.game_id", read_only=True, allow_null=True)
    phase_name = serializers.CharField(source="phase.name", read_only=True)
    nation = serializers.SerializerMethodField()
    total_tokens = serializers.SerializerMethodField()
    latency_ms = serializers.IntegerField(read_only=True, allow_null=True)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_nation(self, obj):
        if obj.member is None or obj.member.nation is None:
            return None
        return obj.member.nation.name

    @extend_schema_field(serializers.IntegerField)
    def get_total_tokens(self, obj):
        return obj.input_tokens + obj.output_tokens


class LLMCallDetailSerializer(LLMCallSummarySerializer):
    system = serializers.CharField(read_only=True)
    user_content = serializers.CharField(read_only=True)
    response = serializers.CharField(read_only=True)
    input_tokens = serializers.IntegerField(read_only=True)
    output_tokens = serializers.IntegerField(read_only=True)
    cache_read_tokens = serializers.IntegerField(read_only=True)
    cache_write_tokens = serializers.IntegerField(read_only=True)
    error_message = serializers.CharField(read_only=True)
