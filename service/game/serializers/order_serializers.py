from rest_framework import serializers


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_type = serializers.CharField()
    source = serializers.CharField()
    target = serializers.CharField(allow_null=True)
    aux = serializers.CharField(allow_null=True)
