from rest_framework import serializers

from game.models import Phase
from common.constants import PhaseStatus
from unit.serializers import UnitSerializer
from supply_center.serializers import SupplyCenterSerializer


class PhaseNationSerializer(serializers.Serializer):
    name = serializers.CharField()


class PhaseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ordinal = serializers.IntegerField()
    season = serializers.CharField()
    year = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
    remaining_time = serializers.SerializerMethodField()
    units = UnitSerializer(many=True)
    supply_centers = SupplyCenterSerializer(many=True)
    options = serializers.DictField()
    status = serializers.ChoiceField(choices=PhaseStatus.STATUS_CHOICES)

    def get_remaining_time(self, obj):
        if isinstance(obj, dict):
            value = obj.get("remaining_time")
            if value is None:
                return None
            # If value is already a number, return it
            if isinstance(value, (int, float)):
                return value
            # If value is a timedelta, convert to seconds
            try:
                return value.total_seconds()
            except Exception:
                return None
        # Fallback for Phase instance
        return obj.remaining_time.total_seconds() if getattr(obj, "remaining_time", None) else None


class PhaseResolveResponseSerializer(serializers.Serializer):
    resolved = serializers.IntegerField()
    failed = serializers.IntegerField()


class PhaseResolveRequestSerializer(serializers.Serializer):
    pass
