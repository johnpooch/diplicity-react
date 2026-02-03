from rest_framework import serializers
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from opentelemetry import trace
from common.constants import NationAssignment, MovementPhaseDuration, PhaseStatus
from member.serializers import MemberSerializer
from unit.models import Unit
from supply_center.models import SupplyCenter

from victory.serializers import VictorySerializer
from variant.models import Variant
from member.models import Member
from .models import Game

tracer = trace.get_tracer(__name__)


class GameListSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    can_join = serializers.SerializerMethodField()
    can_leave = serializers.SerializerMethodField()
    variant_id = serializers.CharField(source="variant.id", read_only=True)
    phases = serializers.SerializerMethodField()
    current_phase_id = serializers.SerializerMethodField()
    private = serializers.BooleanField(read_only=True)
    movement_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    retreat_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    nation_assignment = serializers.CharField(read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    victory = VictorySerializer(read_only=True, allow_null=True)
    sandbox = serializers.BooleanField(read_only=True)
    is_paused = serializers.BooleanField(read_only=True)
    paused_at = serializers.DateTimeField(read_only=True, allow_null=True)

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

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_current_phase_id(self, obj):
        current = obj.current_phase
        return current.id if current else None


class GameRetrieveSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    can_join = serializers.SerializerMethodField()
    can_leave = serializers.SerializerMethodField()
    phases = serializers.SerializerMethodField()
    current_phase_id = serializers.SerializerMethodField()
    members = MemberSerializer(many=True, read_only=True)
    sandbox = serializers.BooleanField(read_only=True)
    victory = VictorySerializer(read_only=True, allow_null=True)
    variant_id = serializers.CharField(source="variant.id", read_only=True)
    nation_assignment = serializers.CharField(read_only=True)
    phase_confirmed = serializers.SerializerMethodField()
    movement_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    retreat_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    private = serializers.BooleanField(read_only=True)
    is_paused = serializers.BooleanField(read_only=True)
    paused_at = serializers.DateTimeField(read_only=True, allow_null=True)

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

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_current_phase_id(self, obj):
        current = obj.current_phase
        return current.id if current else None

    @extend_schema_field(serializers.BooleanField)
    def get_phase_confirmed(self, obj):
        with tracer.start_as_current_span("game.serializers.get_phase_confirmed"):
            return obj.phase_confirmed(self.context["request"].user)

    def to_representation(self, instance):
        with tracer.start_as_current_span("game.serializers.to_representation") as span:
            span.set_attribute("game.id", instance.id)
            span.set_attribute("game.status", instance.status)
            return super().to_representation(instance)


class GameCreateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    variant_id = serializers.CharField()
    nation_assignment = serializers.ChoiceField(choices=NationAssignment.NATION_ASSIGNMENT_CHOICES)
    movement_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES, default=MovementPhaseDuration.TWENTY_FOUR_HOURS
    )
    retreat_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
        required=False,
        allow_null=True,
        default=None,
    )
    private = serializers.BooleanField()

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Variant with this ID does not exist.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        print("validated_data")
        print(validated_data)
        variant = Variant.objects.with_game_creation_data().get(id=validated_data["variant_id"])

        with transaction.atomic():
            game = Game.objects.create_from_template(
                variant,
                name=validated_data["name"],
                nation_assignment=validated_data["nation_assignment"],
                movement_phase_duration=validated_data.get(
                    "movement_phase_duration", MovementPhaseDuration.TWENTY_FOUR_HOURS
                ),
                retreat_phase_duration=validated_data.get("retreat_phase_duration"),
                private=validated_data["private"],
            )

            game.members.create(user=request.user, is_game_master=True)
            game.channels.create(name="Public Press", private=False)

            if hasattr(game, "_created_phase"):
                delattr(game, "_created_phase")

        return Game.objects.all().with_related_data().get(id=game.id)

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data


class GameCreateSandboxSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    variant_id = serializers.CharField()

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Variant with this ID does not exist.")
        return value

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

            nations_list = list(variant.nations.all())
            members_to_create = [Member(game=game, user=request.user) for _ in nations_list]
            created_members = Member.objects.bulk_create(members_to_create)

            current_phase = getattr(game, "_created_phase", None)
            if current_phase is None:
                current_phase = game.phases.first()

            game.start(current_phase=current_phase, members=created_members)

            if hasattr(game, "_created_phase"):
                delattr(game, "_created_phase")

        return Game.objects.all().with_related_data().get(id=game.id)

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data


class GameCloneToSandboxSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)

    def create(self, validated_data):
        request = self.context["request"]
        source_game = self.context["game"]
        source_phase = source_game.current_phase
        user = request.user

        with transaction.atomic():
            user_sandboxes = Game.objects.filter(
                sandbox=True,
                members__user=user
            ).distinct().order_by("created_at")

            if user_sandboxes.count() >= 3:
                oldest_sandbox = user_sandboxes.first()
                oldest_sandbox.delete()

            game = Game.objects.clone_from_phase(
                source_phase,
                name=f"{source_game.name} (Sandbox)",
            )

            nations_list = list(source_game.variant.nations.all())
            members_to_create = [Member(game=game, user=user) for _ in nations_list]
            created_members = Member.objects.bulk_create(members_to_create)

            game.start(current_phase=game._created_phase, members=created_members)

        return Game.objects.all().with_related_data().get(id=game.id)

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data


class GamePauseSerializer(serializers.Serializer):
    def validate(self, attrs):
        if self.instance.is_paused:
            raise serializers.ValidationError("Game is already paused")
        return attrs

    def update(self, instance, validated_data):
        instance.pause()
        return instance

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data


class GameUnpauseSerializer(serializers.Serializer):
    def validate(self, attrs):
        if not self.instance.is_paused:
            raise serializers.ValidationError("Game is not paused")
        return attrs

    def update(self, instance, validated_data):
        instance.unpause()
        return instance

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data
