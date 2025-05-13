from rest_framework import serializers
from .variant_serializers import NationSerializer


class SenderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(source="user.username")
    nation = NationSerializer(source="nation_data")
    is_current_user = serializers.BooleanField()


class MessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    body = serializers.CharField()
    sender = SenderSerializer()
    created_at = serializers.DateTimeField()


class ChannelSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    private = serializers.BooleanField()
    messages = MessageSerializer(many=True)
