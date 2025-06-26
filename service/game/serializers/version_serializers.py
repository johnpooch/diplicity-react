from rest_framework import serializers


class VersionSerializer(serializers.Serializer):
    environment = serializers.CharField()
    version = serializers.CharField()
