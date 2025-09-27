from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from nation.serializers import NationSerializer
from province.serializers import ProvinceSerializer


class UnitSerializer(serializers.Serializer):
    type = serializers.CharField()
    nation = NationSerializer()
    province = ProvinceSerializer()
    dislodged_by = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_dislodged_by(self, obj):
        if obj.dislodged_by:
            return UnitSerializer(obj.dislodged_by).data
        return None
