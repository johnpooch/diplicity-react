from rest_framework import serializers
from .models import Order, OrderResolution


class OrderResolutionSerializer(serializers.Serializer):
    status = serializers.CharField(source="get_status_display")
    by = serializers.CharField(allow_null=True)


class OrderSerializer(serializers.Serializer):
    source = serializers.ReadOnlyField(source="source_display")
    target = serializers.ReadOnlyField(source="target_display")
    aux = serializers.ReadOnlyField(source="aux_display")
    resolution = OrderResolutionSerializer(read_only=True)
    options = serializers.ReadOnlyField(source="options_display")
    order_type = serializers.ReadOnlyField()
    unit_type = serializers.ReadOnlyField()
    nation = serializers.ReadOnlyField()
    complete = serializers.ReadOnlyField(allow_null=True)
    step = serializers.ReadOnlyField(allow_null=True)
    title = serializers.ReadOnlyField(allow_null=True)

    selected = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=False,
    )

    def validate_selected(self, value):
        user = self.context["request"].user
        phase = self.context["phase"]
        order = Order.objects.create_from_selected(user, phase, value)
        order.clean()
        return order.selected

    def create(self, validated_data):
        selected = validated_data["selected"]
        user = self.context["request"].user
        phase = self.context["phase"]
        order = Order.objects.create_from_selected(user, phase, selected)
        if order.complete:
            order.save()
        return order
