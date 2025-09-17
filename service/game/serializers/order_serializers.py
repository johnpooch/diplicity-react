from rest_framework import serializers


class OrderResolutionSerializer(serializers.Serializer):
    status = serializers.CharField(source='get_status_display')
    by = serializers.CharField(allow_null=True)


class OrderProvinceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    supplyCenter = serializers.BooleanField(source='supply_center')


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_type = serializers.CharField()
    source = OrderProvinceSerializer()
    target = OrderProvinceSerializer(allow_null=True)
    aux = OrderProvinceSerializer(allow_null=True)
    resolution = OrderResolutionSerializer(allow_null=True)


class OrderListResponseSerializer(serializers.Serializer):
    nation = serializers.CharField()
    orders = OrderSerializer(many=True)


class OrderOptionSerializer(serializers.Serializer):
    """Serializer for individual order options in interactive creation"""
    value = serializers.CharField()
    label = serializers.CharField()


class InteractiveOrderCreateRequestSerializer(serializers.Serializer):
    """Request serializer for interactive order creation"""
    selected = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        help_text="Array of selected options representing the current order path"
    )


class OrderableProvinceListResponseSerializer(serializers.Serializer):
    province = OrderProvinceSerializer()
    order = OrderSerializer(allow_null=True)


class InteractiveOrderCreateResponseSerializer(serializers.Serializer):
    """
    Response serializer for interactive order creation
    """
    options = OrderOptionSerializer(many=True)
    step = serializers.CharField()
    title = serializers.CharField()
    completed = serializers.BooleanField()
    selected = serializers.ListField(child=serializers.CharField())
    created_order = OrderSerializer(allow_null=True, required=False)
