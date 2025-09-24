from rest_framework import serializers
from province.serializers import ProvinceSerializer
from nation.serializers import NationSerializer


class SupplyCenterSerializer(serializers.Serializer):
    province = ProvinceSerializer()
    nation = NationSerializer()
