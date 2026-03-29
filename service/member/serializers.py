from rest_framework import serializers
from django.apps import apps
from drf_spectacular.utils import extend_schema_field

ChannelMember = apps.get_model("channel", "ChannelMember")


class MemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    picture = serializers.CharField(allow_null=True, read_only=True)
    nation = serializers.CharField(allow_null=True, read_only=True, source="nation.name")
    is_current_user = serializers.SerializerMethodField()
    eliminated = serializers.BooleanField(read_only=True)
    kicked = serializers.BooleanField(read_only=True)
    is_game_master = serializers.BooleanField(read_only=True)
    nmr_extensions_remaining = serializers.IntegerField(read_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_is_current_user(self, obj):
        if obj.user is None:
            return False
        return obj.user == self.context["request"].user

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user
        member = game.members.create(user=user)
        public_channels = game.channels.filter(private=False)
        ChannelMember.objects.bulk_create(
            [ChannelMember(member=member, channel=ch) for ch in public_channels]
        )
        return member
