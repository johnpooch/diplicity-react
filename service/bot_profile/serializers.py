from django.apps import apps
from rest_framework import serializers

from bot_profile.models import BotProfile
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
