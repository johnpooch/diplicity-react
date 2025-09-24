from rest_framework import serializers
from .models import Province


class ProvinceSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id")
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()
