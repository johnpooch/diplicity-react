from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.apps import apps
from .models import Channel, ChannelMessage
from nation.serializers import NationSerializer

Game = apps.get_model("game", "Game")
Member = apps.get_model("member", "Member")


class ChannelMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(source="user.username")
    name = serializers.CharField(source="user.profile.name")
    picture = serializers.CharField(source="user.profile.picture")
    nation = NationSerializer()
    is_current_user = serializers.SerializerMethodField()

    def get_is_current_user(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.user == request.user
        return False


class ChannelMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    body = serializers.CharField(required=True, max_length=1000)
    sender = ChannelMemberSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        channel = self.context["channel"]
        member = self.context["current_game_member"]

        return ChannelMessage.objects.create(
            channel=channel,
            sender=member,
            body=validated_data["body"],
        )


class ChannelSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    private = serializers.BooleanField(read_only=True)
    messages = ChannelMessageSerializer(many=True, read_only=True)

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
