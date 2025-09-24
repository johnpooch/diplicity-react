from rest_framework import serializers
from .models import Nation


class NationSerializer(serializers.Serializer):
    name = serializers.CharField()
    color = serializers.CharField()