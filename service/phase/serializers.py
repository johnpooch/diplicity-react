from rest_framework import serializers
from province.serializers import ProvinceSerializer
from .models import Phase, PhaseState


class PhaseStateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    orders_confirmed = serializers.BooleanField(read_only=True)
    eliminated = serializers.BooleanField(read_only=True)
    orderable_provinces = ProvinceSerializer(read_only=True, many=True)

    def update(self, instance, validated_data):
        instance.orders_confirmed = not instance.orders_confirmed
        instance.save()
        return instance
