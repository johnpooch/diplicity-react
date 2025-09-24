from rest_framework import serializers
from .models import Province


class ProvinceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()