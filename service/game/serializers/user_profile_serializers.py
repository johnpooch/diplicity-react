from rest_framework import serializers


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    picture = serializers.CharField()
    username = serializers.CharField()
    email = serializers.CharField()
