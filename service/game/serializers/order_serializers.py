from rest_framework import serializers


class OrderResolutionSerializer(serializers.Serializer):
    status = serializers.CharField(source="get_status_display")
    by = serializers.CharField(allow_null=True)


class OrderProvinceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    supplyCenter = serializers.BooleanField(source="supply_center")


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_type = serializers.CharField()
    source = OrderProvinceSerializer(source="source_display")
    target = OrderProvinceSerializer(source="target_display", allow_null=True)
    aux = OrderProvinceSerializer(source="aux_display", allow_null=True)
    unit_type = serializers.CharField(allow_null=True)
    resolution = OrderResolutionSerializer(allow_null=True)


class OrderableProvinceListResponseSerializer(serializers.Serializer):
    province = OrderProvinceSerializer()
    order = OrderSerializer(allow_null=True)
