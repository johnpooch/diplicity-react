from rest_framework import serializers
from .game_serializers import ProvinceSerializer, UnitSerializer


class OptionSerializer(serializers.Serializer):
    province = ProvinceSerializer()
    unit = UnitSerializer(required=False, allow_null=True)
