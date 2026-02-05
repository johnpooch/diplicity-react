from zoneinfo import ZoneInfo

from rest_framework import serializers
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from opentelemetry import trace
from common.constants import DeadlineMode, NationAssignment, MovementPhaseDuration, PhaseFrequency, PhaseStatus
from member.serializers import MemberSerializer
from unit.models import Unit
from supply_center.models import SupplyCenter
from notification import signals as notification_signals

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
    nmr_extensions_allowed = serializers.IntegerField(read_only=True)
    deadline_mode = serializers.CharField(read_only=True)
    fixed_deadline_time = serializers.TimeField(read_only=True, allow_null=True)
    fixed_deadline_timezone = serializers.CharField(read_only=True, allow_null=True)
    movement_frequency = serializers.CharField(read_only=True, allow_null=True)
    retreat_frequency = serializers.CharField(read_only=True, allow_null=True)

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
    nmr_extensions_allowed = serializers.IntegerField(read_only=True)
    deadline_mode = serializers.CharField(read_only=True)
    fixed_deadline_time = serializers.TimeField(read_only=True, allow_null=True)
    fixed_deadline_timezone = serializers.CharField(read_only=True, allow_null=True)
    movement_frequency = serializers.CharField(read_only=True, allow_null=True)
    retreat_frequency = serializers.CharField(read_only=True, allow_null=True)

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
    deadline_mode = serializers.ChoiceField(
        choices=DeadlineMode.DEADLINE_MODE_CHOICES,
        default=DeadlineMode.DURATION,
    )
    fixed_deadline_time = serializers.TimeField(required=False, allow_null=True, default=None)
    fixed_deadline_timezone = serializers.CharField(required=False, allow_null=True, default=None, max_length=50)
    movement_frequency = serializers.ChoiceField(
        choices=PhaseFrequency.PHASE_FREQUENCY_CHOICES,
        required=False,
        allow_null=True,
        default=None,
    )
    retreat_frequency = serializers.ChoiceField(
        choices=PhaseFrequency.PHASE_FREQUENCY_CHOICES,
        required=False,
        allow_null=True,
        default=None,
    )
    nmr_extensions_allowed = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        max_value=2,
    )

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Variant with this ID does not exist.")
        return value

    def validate_fixed_deadline_timezone(self, value):
        if value is not None:
            try:
                ZoneInfo(value)
            except KeyError:
                raise serializers.ValidationError(f"Invalid timezone: {value}")
        return value

    def validate(self, attrs):
        deadline_mode = attrs.get("deadline_mode", DeadlineMode.DURATION)

        if deadline_mode == DeadlineMode.FIXED_TIME:
            if not attrs.get("fixed_deadline_time"):
                raise serializers.ValidationError({
                    "fixed_deadline_time": "Required when deadline_mode is 'fixed_time'."
                })
            if not attrs.get("fixed_deadline_timezone"):
                raise serializers.ValidationError({
                    "fixed_deadline_timezone": "Required when deadline_mode is 'fixed_time'."
                })
            if not attrs.get("movement_frequency"):
                raise serializers.ValidationError({
                    "movement_frequency": "Required when deadline_mode is 'fixed_time'."
                })
        else:
            attrs["fixed_deadline_time"] = None
            attrs["fixed_deadline_timezone"] = None
            attrs["movement_frequency"] = None
            attrs["retreat_frequency"] = None

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        variant = Variant.objects.with_game_creation_data().get(id=validated_data["variant_id"])

        with transaction.atomic():
            game = Game.objects.create_from_template(
                variant,
                name=validated_data["name"],
                nation_assignment=validated_data["nation_assignment"],
                movement_phase_duration=validated_data["movement_phase_duration"],
                retreat_phase_duration=validated_data.get("retreat_phase_duration"),
                private=validated_data["private"],
                deadline_mode=validated_data["deadline_mode"],
                fixed_deadline_time=validated_data.get("fixed_deadline_time"),
                fixed_deadline_timezone=validated_data.get("fixed_deadline_timezone"),
                movement_frequency=validated_data.get("movement_frequency"),
                retreat_frequency=validated_data.get("retreat_frequency"),
                nmr_extensions_allowed=validated_data["nmr_extensions_allowed"],
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
        gm_username = self.context["request"].user.username
        instance.pause()

        def send_notification():
            user_ids = [member.user.id for member in instance.members.all()]
            notification_signals.send_notification_to_users(
                user_ids=user_ids,
                title="Game Paused",
                body=f"Game paused by Game Master ({gm_username})",
                notification_type="game_paused",
                data={"game_id": str(instance.id)},
            )

        transaction.on_commit(send_notification)
        return instance

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data


class GameUnpauseSerializer(serializers.Serializer):
    def validate(self, attrs):
        if not self.instance.is_paused:
            raise serializers.ValidationError("Game is not paused")
        return attrs

    def update(self, instance, validated_data):
        gm_username = self.context["request"].user.username
        instance.unpause()

        def send_notification():
            user_ids = [member.user.id for member in instance.members.all()]
            new_deadline = instance.current_phase.scheduled_resolution if instance.current_phase else None
            deadline_str = new_deadline.strftime("%b %d, %Y at %I:%M %p") if new_deadline else "N/A"
            notification_signals.send_notification_to_users(
                user_ids=user_ids,
                title="Game Resumed",
                body=f"Game resumed by Game Master ({gm_username}). New deadline: {deadline_str}",
                notification_type="game_resumed",
                data={"game_id": str(instance.id)},
            )

        transaction.on_commit(send_notification)
        return instance

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data


class GameExtendDeadlineSerializer(serializers.Serializer):
    duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
    )

    def validate(self, attrs):
        if "duration" not in attrs:
            raise serializers.ValidationError({"duration": ["This field is required."]})
        if self.instance.is_paused:
            raise serializers.ValidationError("Cannot extend deadline while game is paused")
        current_phase = self.instance.current_phase
        if not current_phase or not current_phase.scheduled_resolution:
            raise serializers.ValidationError("No active phase with a scheduled resolution")
        return attrs

    def update(self, instance, validated_data):
        gm_username = self.context["request"].user.username
        instance.extend_deadline(validated_data["duration"])

        def send_notification():
            user_ids = [member.user.id for member in instance.members.all()]
            notification_signals.send_notification_to_users(
                user_ids=user_ids,
                title="Deadline Extended",
                body=f"Deadline extended by Game Master ({gm_username})",
                notification_type="game_deadline_extended",
                data={"game_id": str(instance.id)},
            )

        transaction.on_commit(send_notification)
        return instance

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data
