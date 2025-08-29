from rest_framework import serializers

from .phase_serializers import PhaseSerializer
from .variant_serializers import VariantSerializer


class MemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    picture = serializers.CharField()
    nation = serializers.CharField()
    is_current_user = serializers.BooleanField()



class GameSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    status = serializers.CharField()
    movement_phase_duration = serializers.CharField()
    nation_assignment = serializers.CharField()
    can_join = serializers.BooleanField()
    can_leave = serializers.BooleanField()
    phases = PhaseSerializer(many=True)
    members = MemberSerializer(many=True)
    variant = VariantSerializer()
    phase_confirmed = serializers.BooleanField()
    can_confirm_phase = serializers.BooleanField()
