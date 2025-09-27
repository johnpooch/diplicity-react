from rest_framework import serializers
from province.serializers import ProvinceSerializer
from nation.serializers import NationSerializer
from unit.serializers import UnitSerializer
from supply_center.serializers import SupplyCenterSerializer


class PhaseSerializer(serializers.Serializer):
    season = serializers.CharField()
    year = serializers.IntegerField()
    type = serializers.CharField()
    units = UnitSerializer(many=True)
    supply_centers = SupplyCenterSerializer(many=True)


class VariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = NationSerializer(many=True)
    provinces = ProvinceSerializer(many=True)
    template_phase = PhaseSerializer()
