from rest_framework import serializers
from province.serializers import ProvinceSerializer
from nation.serializers import NationSerializer
from .models import Order
from common.constants import OrderType, UnitType, OrderCreationStep


class OrderOptionSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class OrderResolutionSerializer(serializers.Serializer):
    status = serializers.CharField(source="get_status_display")
    by = ProvinceSerializer(allow_null=True)


class OrderSerializer(serializers.Serializer):
    source = ProvinceSerializer(read_only=True)
    target = ProvinceSerializer(read_only=True)
    aux = ProvinceSerializer(read_only=True)
    resolution = OrderResolutionSerializer(read_only=True)
    options = OrderOptionSerializer(source="options_display", read_only=True, many=True)
    order_type = serializers.ChoiceField(choices=OrderType.ORDER_TYPE_CHOICES, read_only=True)
    unit_type = serializers.ChoiceField(choices=UnitType.UNIT_TYPE_CHOICES, read_only=True)
    nation = NationSerializer(read_only=True)
    complete = serializers.BooleanField(allow_null=True, read_only=True)
    step = serializers.ChoiceField(
        choices=OrderCreationStep.ORDER_CREATION_STEP_CHOICES, allow_null=True, read_only=True
    )
    title = serializers.CharField(allow_null=True, read_only=True)

    selected = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=False,
    )

    def validate_selected(self, value):
        order = Order.objects.create_from_selected(self.context["request"].user, self.context["phase"], value)
        order.clean()
        return order.selected

    def create(self, validated_data):
        order = Order.objects.create_from_selected(
            self.context["request"].user, self.context["phase"], validated_data["selected"]
        )
        if order.complete:
            Order.objects.delete_existing_for_source(order.phase_state, order.source)
            order.save()
        return order
