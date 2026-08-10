from django.apps import apps
from rest_framework import serializers

from bot_profile.models import BotProfile
from member.serializers import MemberSerializer

ChannelMember = apps.get_model("channel", "ChannelMember")


class AvailableBotSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(source="user.profile.name", read_only=True)
    picture = serializers.CharField(source="user.profile.picture", read_only=True, allow_null=True)
    kind = serializers.CharField(read_only=True)


class BotMemberCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(write_only=True)

    def _resolve_available_bot(self, user_id):
        game = self.context["game"]
        bot_profile = (
            BotProfile.objects.available_for_game(game).filter(user_id=user_id).first()
        )
        if bot_profile is None:
            raise serializers.ValidationError(
                "This bot is not available to add to this game."
            )
        return bot_profile

    def validate_user_id(self, value):
        self._resolve_available_bot(value)
        return value

    def create(self, validated_data):
        game = self.context["game"]
        bot_profile = self._resolve_available_bot(validated_data["user_id"])
        member = game.members.create(user=bot_profile.user)
        public_channels = game.channels.filter(private=False)
        ChannelMember.objects.bulk_create(
            [ChannelMember(member=member, channel=ch) for ch in public_channels]
        )
        return member

    def to_representation(self, instance):
        return MemberSerializer(instance, context=self.context).data
