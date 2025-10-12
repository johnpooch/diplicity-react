from rest_framework import serializers
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from common.constants import NationAssignment, MovementPhaseDuration
from variant.serializers import VariantSerializer
from phase.serializers import PhaseSerializer
from member.serializers import MemberSerializer
from variant.models import Variant
from .models import Game


class GameSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    can_join = serializers.SerializerMethodField()
    can_leave = serializers.SerializerMethodField()
    phases = PhaseSerializer(many=True, read_only=True)
    variant = VariantSerializer(read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    phase_confirmed = serializers.SerializerMethodField()

    name = serializers.CharField()
    variant_id = serializers.CharField(write_only=True)
    nation_assignment = serializers.ChoiceField(choices=NationAssignment.NATION_ASSIGNMENT_CHOICES)
    movement_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
        default=MovementPhaseDuration.TWENTY_FOUR_HOURS
    )
    private = serializers.BooleanField()

    @extend_schema_field(serializers.BooleanField)
    def get_can_join(self, obj):
        return obj.can_join(self.context["request"].user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_leave(self, obj):
        return obj.can_leave(self.context["request"].user)

    @extend_schema_field(serializers.BooleanField)
    def get_phase_confirmed(self, obj):
        return obj.phase_confirmed(self.context["request"].user)

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Variant with this ID does not exist.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        variant = Variant.objects.get(id=validated_data["variant_id"])

        with transaction.atomic():
            return Game.objects.create_from_template(
                variant,
                request.user,
                name=validated_data["name"],
                nation_assignment=validated_data["nation_assignment"],
                movement_phase_duration=validated_data.get("movement_phase_duration", MovementPhaseDuration.TWENTY_FOUR_HOURS),
                private=validated_data["private"],
            )
