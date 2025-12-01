from rest_framework import serializers
from django.core import exceptions
from order.utils import get_options_for_order
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
    named_coast = ProvinceSerializer(read_only=True)
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
    summary = serializers.CharField(allow_null=True, read_only=True)

    selected = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=False,
    )

    def validate_selected(self, value):
        phase = self.context["phase"]
        province_lookup = {p.province_id: p for p in phase.variant.provinces.all()}
        self.context["_province_lookup"] = province_lookup

        order = Order.objects.create_from_selected(
            self.context["request"].user, phase, value, province_lookup=province_lookup
        )
        try:
            get_options_for_order(order.phase.transformed_options, order)
        except Exception as e:
            raise exceptions.ValidationError(e)
        return order.selected

    def create(self, validated_data):
        province_lookup = self.context.get("_province_lookup")
        if province_lookup is None:
            province_lookup = {p.province_id: p for p in self.context["phase"].variant.provinces.all()}

        order = Order.objects.create_from_selected(
            self.context["request"].user, self.context["phase"], validated_data["selected"], province_lookup=province_lookup
        )
        if order.complete:
            Order.objects.delete_existing_for_source(order.phase_state, order.source)
            order.save()
            return Order.objects.with_related_data().get(id=order.id)

        return order
