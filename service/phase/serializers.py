from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from common.constants import PhaseStatus
from common.permissions import IsCurrentPhaseActive
from common.serializers import derived, hydrated
from emit import emit
from member.serializers import MemberSerializer
from phase.loaders import PhaseRetrieveLoader, PhaseStateLoader
from phase.models import Phase
from province.serializers import ProvinceSerializer
from supply_center.serializers import SupplyCenterSerializer
from unit.serializers import UnitSerializer


class PhaseStateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    orders_confirmed = serializers.BooleanField(read_only=True)
    eliminated = serializers.BooleanField(read_only=True)
    orderable_provinces = ProvinceSerializer(read_only=True, many=True)
    member = MemberSerializer(read_only=True)
    max_orders = derived(serializers.IntegerField(read_only=True, allow_null=True))

    class Meta:
        loader = PhaseStateLoader

    def update(self, instance, validated_data):
        with transaction.atomic():
            if Phase.objects.lock_if_active(instance.phase_id) is None:
                raise serializers.ValidationError(IsCurrentPhaseActive.message)

            instance.orders_confirmed = not instance.orders_confirmed
            instance.save()

            if instance.orders_confirmed:
                emit("phase_state_confirmed", phase=instance.phase)

            Phase.objects.arm_resolution(instance.phase)

        return instance


class PhaseListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ordinal = serializers.IntegerField()
    season = serializers.CharField()
    year = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
    status = serializers.ChoiceField(choices=PhaseStatus.STATUS_CHOICES)


class PhaseRevertSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.revert_to_this_phase()
        return instance

    def to_representation(self, instance):
        return PhaseListSerializer(instance, context=self.context).data


@extend_schema_field(OpenApiTypes.STR)
class ProvinceNationsField(serializers.JSONField):
    pass


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
    province_nations = hydrated(ProvinceNationsField(read_only=True))

    class Meta:
        loader = PhaseRetrieveLoader
