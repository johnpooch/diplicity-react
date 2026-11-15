from rest_framework import serializers


class ProvinceSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id")
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()
    parent_id = serializers.CharField(source="parent.province_id", allow_null=True)
    named_coast_ids = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )
