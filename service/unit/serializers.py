from rest_framework import serializers
from nation.serializers import NationSerializer
from province.serializers import ProvinceSerializer


class UnitSerializer(serializers.Serializer):
    type = serializers.CharField()
    nation = NationSerializer()
    province = ProvinceSerializer()
    dislodged = serializers.BooleanField()
    dislodged_by = serializers.SerializerMethodField()

    def get_dislodged_by(self, obj):
        if obj.dislodged_by:
            return UnitSerializer(obj.dislodged_by).data
        return None
