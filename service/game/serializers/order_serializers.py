from rest_framework import serializers


class OrderResolutionSerializer(serializers.Serializer):
    status = serializers.CharField(source='get_status_display')
    by = serializers.CharField(allow_null=True)


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_type = serializers.CharField()
    source = serializers.CharField()
    target = serializers.CharField(allow_null=True)
    aux = serializers.CharField(allow_null=True)
    resolution = OrderResolutionSerializer(allow_null=True)


class NationOrderSerializer(serializers.Serializer):
    nation = serializers.CharField()
    orders = OrderSerializer(many=True)
