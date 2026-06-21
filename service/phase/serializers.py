from django.db import transaction
from rest_framework import serializers
from common.constants import PhaseStatus
from member.serializers import MemberSerializer
from phase.tasks import resolve_phase
from phase.utils import compute_province_nations
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
        with transaction.atomic():
            instance.orders_confirmed = not instance.orders_confirmed
            instance.save()

            if instance.orders_confirmed:
                resolve_phase.configure(
                    lock=f"resolve-game-{instance.phase.game_id}",
                ).defer(phase_id=instance.phase_id)

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
    early_resolve_window_end = serializers.DateTimeField(allow_null=True)
    status = serializers.ChoiceField(choices=PhaseStatus.STATUS_CHOICES)
    units = UnitSerializer(many=True)
    supply_centers = SupplyCenterSerializer(many=True)
    previous_phase_id = serializers.IntegerField(allow_null=True)
    next_phase_id = serializers.IntegerField(allow_null=True)
    province_nations = serializers.SerializerMethodField()

    def get_province_nations(self, phase):
        return compute_province_nations(
            phase.supply_centers.all(),
            phase.variant.provinces.all(),
            phase.variant.dominance_rules,
            phase.variant.nations.all(),
        )
