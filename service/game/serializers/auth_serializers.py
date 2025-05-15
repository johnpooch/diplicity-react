from rest_framework import serializers


class AuthSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.CharField()
    username = serializers.CharField()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
