from rest_framework import serializers
from common.constants import PhaseStatus
from member.serializers import MemberSerializer
from province.serializers import ProvinceSerializer
from supply_center.serializers import SupplyCenterSerializer
from unit.serializers import UnitSerializer


class PhaseResolveResponseSerializer(serializers.Serializer):
    resolved = serializers.IntegerField()
    failed = serializers.IntegerField()


class PhaseStateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    orders_confirmed = serializers.BooleanField(read_only=True)
    eliminated = serializers.BooleanField(read_only=True)
    orderable_provinces = ProvinceSerializer(read_only=True, many=True)
    member = MemberSerializer(read_only=True)

    def update(self, instance, validated_data):
        instance.orders_confirmed = not instance.orders_confirmed
        instance.save()
        return instance


class PhaseListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ordinal = serializers.IntegerField()
    season = serializers.CharField()
    year = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
    status = serializers.ChoiceField(choices=PhaseStatus.STATUS_CHOICES)


class PhaseRetrieveSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ordinal = serializers.IntegerField()
    season = serializers.CharField()
    year = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
    remaining_time = serializers.IntegerField(source="remaining_time_seconds")
    scheduled_resolution = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=PhaseStatus.STATUS_CHOICES)
    units = UnitSerializer(many=True)
    supply_centers = SupplyCenterSerializer(many=True)
    previous_phase_id = serializers.IntegerField(allow_null=True)
    next_phase_id = serializers.IntegerField(allow_null=True)
