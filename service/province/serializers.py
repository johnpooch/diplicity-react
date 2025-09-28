from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Province


class ProvinceSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id")
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()
    parent_id = serializers.CharField(source="parent.province_id", allow_null=True)
    named_coast_ids = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_named_coast_ids(self, obj):
        return [coast.province_id for coast in obj.named_coasts.all()]
