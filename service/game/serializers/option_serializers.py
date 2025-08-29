from rest_framework import serializers
from .phase_serializers import ProvinceSerializer, UnitSerializer


class PartialOrderSerializer(serializers.Serializer):
    source = serializers.CharField(required=False, allow_null=True)
    target = serializers.CharField(required=False, allow_null=True)
    aux = serializers.CharField(required=False, allow_null=True)
    order_type = serializers.CharField(required=False, allow_null=True)


class OptionSerializer(serializers.Serializer):
    province = ProvinceSerializer()
    unit = UnitSerializer(required=False, allow_null=True)


class ListOptionsRequestSerializer(serializers.Serializer):
    order = PartialOrderSerializer()