from rest_framework import serializers
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from opentelemetry import trace
from common.constants import NationAssignment, MovementPhaseDuration
from variant.serializers import VariantSerializer
from phase.serializers import PhaseSerializer
from member.serializers import MemberSerializer

from victory.serializers import VictorySerializer
from variant.models import Variant
from phase.models import Phase
from member.models import Member
from .models import Game

tracer = trace.get_tracer(__name__)


class BaseGameSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    can_join = serializers.SerializerMethodField()
    can_leave = serializers.SerializerMethodField()
    phases = PhaseSerializer(many=True, read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    sandbox = serializers.BooleanField(read_only=True)
    victory = VictorySerializer(read_only=True, allow_null=True)

    name = serializers.CharField()
    variant_id = serializers.CharField(write_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_can_join(self, obj):
        with tracer.start_as_current_span("game.serializers.get_can_join"):
            return obj.can_join(self.context["request"].user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_leave(self, obj):
        with tracer.start_as_current_span("game.serializers.get_can_leave"):
            return obj.can_leave(self.context["request"].user)

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Variant with this ID does not exist.")
        return value

    def to_representation(self, instance):
        with tracer.start_as_current_span("game.serializers.to_representation") as span:
            span.set_attribute("game.id", instance.id)
            span.set_attribute("game.status", instance.status)
            return super().to_representation(instance)


class GameListSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    can_join = serializers.SerializerMethodField(read_only=True)
    can_leave = serializers.SerializerMethodField(read_only=True)
    variant_id = serializers.CharField(source="variant.id", read_only=True)
    phases = serializers.SerializerMethodField()
    private = serializers.BooleanField(read_only=True)
    movement_phase_duration = serializers.CharField(read_only=True)
    nation_assignment = serializers.CharField(read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    victory = VictorySerializer(read_only=True, allow_null=True)
    sandbox = serializers.BooleanField(read_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_can_join(self, obj):
        with tracer.start_as_current_span("game.serializers.get_can_join"):
            return obj.can_join(self.context["request"].user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_leave(self, obj):
        with tracer.start_as_current_span("game.serializers.get_can_leave"):
            return obj.can_leave(self.context["request"].user)

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField()))
    def get_phases(self, obj):
        return [phase.id for phase in obj.phases.all()]


class GameSerializer(BaseGameSerializer):
    variant = VariantSerializer(read_only=True)
    nation_assignment = serializers.ChoiceField(choices=NationAssignment.NATION_ASSIGNMENT_CHOICES)
    phase_confirmed = serializers.SerializerMethodField()
    movement_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES, default=MovementPhaseDuration.TWENTY_FOUR_HOURS
    )
    private = serializers.BooleanField()

    @extend_schema_field(serializers.BooleanField)
    def get_phase_confirmed(self, obj):
        with tracer.start_as_current_span("game.serializers.get_phase_confirmed"):
            return obj.phase_confirmed(self.context["request"].user)

    def create(self, validated_data):
        request = self.context["request"]
        variant = Variant.objects.with_game_creation_data().get(id=validated_data["variant_id"])

        with transaction.atomic():
            game = Game.objects.create_from_template(
                variant,
                name=validated_data["name"],
                nation_assignment=validated_data["nation_assignment"],
                movement_phase_duration=validated_data.get(
                    "movement_phase_duration", MovementPhaseDuration.TWENTY_FOUR_HOURS
                ),
                private=validated_data["private"],
            )

            game.members.create(user=request.user)
            game.channels.create(name="Public Press", private=False)

            # Clean up temporary attribute
            if hasattr(game, "_created_phase"):
                delattr(game, "_created_phase")

        # Reload game with prefetched data to avoid n+1 queries during serialization
        return Game.objects.all().with_related_data().get(id=game.id)


class SandboxGameSerializer(BaseGameSerializer):
    variant = VariantSerializer(read_only=True)
    nation_assignment = serializers.ChoiceField(choices=NationAssignment.NATION_ASSIGNMENT_CHOICES, read_only=True)
    movement_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES, read_only=True
    )
    private = serializers.BooleanField(read_only=True)

    def create(self, validated_data):
        request = self.context["request"]
        variant = Variant.objects.with_game_creation_data().get(id=validated_data["variant_id"])

        with transaction.atomic():
            game = Game.objects.create_from_template(
                variant,
                name=validated_data["name"],
                sandbox=True,
                private=True,
                nation_assignment=NationAssignment.ORDERED,
                movement_phase_duration=None,
            )

            # Bulk create members to avoid n+1 queries
            nations_list = list(variant.nations.all())
            members_to_create = [Member(game=game, user=request.user) for _ in nations_list]
            created_members = Member.objects.bulk_create(members_to_create)

            # Get the phase we just created from create_from_template to avoid querying for it
            # create_from_template stores it on game._created_phase
            current_phase = getattr(game, "_created_phase", None)
            if current_phase is None:
                current_phase = game.phases.first()

            game.start(current_phase=current_phase, members=created_members)

            # Clean up temporary attribute
            if hasattr(game, "_created_phase"):
                delattr(game, "_created_phase")

        # Reload game with prefetched data to avoid n+1 queries during serialization
        return Game.objects.all().with_related_data().get(id=game.id)
