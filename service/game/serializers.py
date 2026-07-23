from zoneinfo import ZoneInfo

from rest_framework import serializers
from django.db import transaction
from django.db.models import Subquery, OuterRef
from django.apps import apps
from drf_spectacular.utils import extend_schema_field
from opentelemetry import trace
from common.constants import Commitment, CommitmentEligibility, CommitmentRequirement, DeadlineMode, MinReliability, NationAssignment, MovementPhaseDuration, PhaseFrequency, PhaseStatus, PressType, VariantStatus
from user_profile.commitment import commitment_allows_requirement
from member.serializers import MemberSerializer
from unit.models import Unit
from supply_center.models import SupplyCenter
from emit import emit

from victory.serializers import VictorySerializer
from variant.models import Variant
from member.models import Member
from .models import Game

ChannelMember = apps.get_model("channel", "ChannelMember")
ChannelMessage = apps.get_model("channel", "ChannelMessage")

tracer = trace.get_tracer(__name__)


def _phase_state_order_count(phase_state):
    count = getattr(phase_state, "order_count", None)
    if count is None:
        count = phase_state.orders.count()
    return count


class GameMasterSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="id", read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)
    picture = serializers.CharField(source="profile.picture", read_only=True, allow_null=True)


class GameListBoardNationSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)


class GameListBoardProvinceSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id", read_only=True)


class GameListUnitSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True)
    nation = GameListBoardNationSerializer(read_only=True)
    province = GameListBoardProvinceSerializer(read_only=True)
    dislodged = serializers.BooleanField(read_only=True)


class GameListSupplyCenterSerializer(serializers.Serializer):
    nation = GameListBoardNationSerializer(read_only=True)
    province = GameListBoardProvinceSerializer(read_only=True)


class GameListCurrentPhaseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    ordinal = serializers.IntegerField(read_only=True)
    season = serializers.CharField(read_only=True)
    year = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    scheduled_resolution = serializers.DateTimeField(read_only=True, allow_null=True)
    remaining_time = serializers.IntegerField(source="remaining_time_seconds", read_only=True)
    units = GameListUnitSerializer(many=True, read_only=True)
    supply_centers = GameListSupplyCenterSerializer(many=True, read_only=True)


class GameListSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    can_join = serializers.SerializerMethodField()
    can_leave = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    game_master = GameMasterSerializer(allow_null=True, read_only=True)
    variant_id = serializers.CharField(source="variant.id", read_only=True)
    phases = serializers.SerializerMethodField()
    current_phase_id = serializers.SerializerMethodField()
    current_phase = serializers.SerializerMethodField()
    phase_confirmed = serializers.SerializerMethodField()
    order_status = serializers.SerializerMethodField()
    member_status = serializers.SerializerMethodField()
    private = serializers.BooleanField(read_only=True)
    anonymous = serializers.BooleanField(read_only=True)
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
    press_type = serializers.CharField(read_only=True)
    min_reliability = serializers.CharField(read_only=True)
    commitment_requirement = serializers.CharField(read_only=True)
    commitment_eligibility = serializers.SerializerMethodField()
    total_unread_message_count = serializers.IntegerField(read_only=True, default=0)

    @extend_schema_field(serializers.BooleanField)
    def get_can_join(self, obj):
        with tracer.start_as_current_span("game.serializers.get_can_join"):
            user = self.context["request"].user
            if not user.is_authenticated:
                return False
            return obj.can_join(user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_leave(self, obj):
        with tracer.start_as_current_span("game.serializers.get_can_leave"):
            user = self.context["request"].user
            if not user.is_authenticated:
                return False
            return obj.can_leave(user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_delete(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return obj.can_delete(user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_manage(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return obj.can_manage(user)

    @extend_schema_field(serializers.ChoiceField(
        choices=[
            CommitmentEligibility.ELIGIBLE,
            CommitmentEligibility.COMMITTED_LOCKED,
            CommitmentEligibility.LOW_LOCKED,
        ],
        allow_null=True,
    ))
    def get_commitment_eligibility(self, obj):
        return obj.commitment_eligibility(self.context["request"].user)

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField()))
    def get_phases(self, obj):
        return [phase.id for phase in obj.phases.all()]

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_current_phase_id(self, obj):
        current = obj.current_phase
        return current.id if current else None

    @extend_schema_field(GameListCurrentPhaseSerializer(allow_null=True))
    def get_current_phase(self, obj):
        current = obj.current_phase
        return GameListCurrentPhaseSerializer(current).data if current else None

    @extend_schema_field(serializers.BooleanField)
    def get_phase_confirmed(self, obj):
        with tracer.start_as_current_span("game.serializers.get_phase_confirmed"):
            user = self.context["request"].user
            if not user.is_authenticated:
                return False
            return obj.phase_confirmed(user)

    @extend_schema_field(serializers.ChoiceField(
        choices=["orders_required", "orders_submitted", "orders_not_confirmed", "no_orders_required"],
        allow_null=True,
    ))
    def get_order_status(self, obj):
        if obj.sandbox:
            return None
        user = self.context["request"].user
        if not user.is_authenticated or obj.status != "active":
            return None
        current_phase = obj.current_phase
        if current_phase is None:
            return None
        for phase_state in current_phase.phase_states.all():
            if phase_state.member.user_id == user.id:
                if phase_state.orders_confirmed:
                    return "orders_submitted"
                if not phase_state.has_possible_orders:
                    return "no_orders_required"
                if _phase_state_order_count(phase_state) == 0:
                    return "orders_required"
                if obj.deadline_mode == DeadlineMode.FIXED_TIME:
                    return "orders_submitted"
                return "orders_not_confirmed"
        return None

    @extend_schema_field(serializers.ListField(
        child=serializers.ChoiceField(choices=["nmr", "civil_disorder"]),
        allow_null=True,
    ))
    def get_member_status(self, obj):
        if obj.sandbox:
            return None
        user = self.context["request"].user
        if not user.is_authenticated:
            return []
        current_member = next(
            (m for m in obj.members.all() if m.user_id == user.id), None
        )
        if current_member is None:
            return []
        statuses = []
        if current_member.civil_disorder:
            statuses.append("civil_disorder")
        phases = list(obj.phases.all())
        completed_phases = [p for p in phases if p.status == "completed"]
        if completed_phases:
            prev_phase = max(completed_phases, key=lambda p: p.ordinal)
            for phase_state in prev_phase.phase_states.all():
                if phase_state.member.user_id == user.id:
                    if phase_state.orders_outcome == "nmr":
                        statuses.append("nmr")
                    break
        return statuses


class GameFindSimilarSerializer(serializers.Serializer):
    game = GameListSerializer(allow_null=True)


class GameRetrieveSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    can_join = serializers.SerializerMethodField()
    can_leave = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    game_master = GameMasterSerializer(allow_null=True, read_only=True)
    phases = serializers.SerializerMethodField()
    current_phase_id = serializers.SerializerMethodField()
    members = MemberSerializer(many=True, read_only=True)
    sandbox = serializers.BooleanField(read_only=True)
    victory = VictorySerializer(read_only=True, allow_null=True)
    variant_id = serializers.CharField(source="variant.id", read_only=True)
    nation_assignment = serializers.CharField(read_only=True)
    phase_confirmed = serializers.SerializerMethodField()
    order_status = serializers.SerializerMethodField()
    member_status = serializers.SerializerMethodField()
    movement_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    retreat_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    private = serializers.BooleanField(read_only=True)
    anonymous = serializers.BooleanField(read_only=True)
    is_paused = serializers.BooleanField(read_only=True)
    paused_at = serializers.DateTimeField(read_only=True, allow_null=True)
    nmr_extensions_allowed = serializers.IntegerField(read_only=True)
    deadline_mode = serializers.CharField(read_only=True)
    fixed_deadline_time = serializers.TimeField(read_only=True, allow_null=True)
    fixed_deadline_timezone = serializers.CharField(read_only=True, allow_null=True)
    movement_frequency = serializers.CharField(read_only=True, allow_null=True)
    retreat_frequency = serializers.CharField(read_only=True, allow_null=True)
    press_type = serializers.CharField(read_only=True)
    min_reliability = serializers.CharField(read_only=True)
    commitment_requirement = serializers.CharField(read_only=True)
    commitment_eligibility = serializers.SerializerMethodField()
    total_unread_message_count = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ChoiceField(
        choices=[
            CommitmentEligibility.ELIGIBLE,
            CommitmentEligibility.COMMITTED_LOCKED,
            CommitmentEligibility.LOW_LOCKED,
        ],
        allow_null=True,
    ))
    def get_commitment_eligibility(self, obj):
        return obj.commitment_eligibility(self.context["request"].user)

    @extend_schema_field(serializers.IntegerField)
    def get_total_unread_message_count(self, obj):
        annotated = getattr(obj, "total_unread_message_count", None)
        if annotated is not None:
            return annotated
        user = self.context["request"].user
        if not user.is_authenticated:
            return 0
        return (
            ChannelMessage.objects.filter(
                channel__game=obj,
                channel__member_channels__member__user=user,
                created_at__gt=Subquery(
                    ChannelMember.objects.filter(
                        channel=OuterRef("channel"),
                        member__user=user,
                    ).values("last_read_at")[:1]
                ),
            )
            .exclude(sender__user=user)
            .distinct()
            .count()
        )

    @extend_schema_field(serializers.BooleanField)
    def get_can_join(self, obj):
        with tracer.start_as_current_span("game.serializers.get_can_join"):
            user = self.context["request"].user
            if not user.is_authenticated:
                return False
            return obj.can_join(user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_leave(self, obj):
        with tracer.start_as_current_span("game.serializers.get_can_leave"):
            user = self.context["request"].user
            if not user.is_authenticated:
                return False
            return obj.can_leave(user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_delete(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return obj.can_delete(user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_manage(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return obj.can_manage(user)

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
            user = self.context["request"].user
            if not user.is_authenticated:
                return False
            return obj.phase_confirmed(user)

    @extend_schema_field(serializers.ChoiceField(
        choices=["orders_required", "orders_submitted", "orders_not_confirmed", "no_orders_required"],
        allow_null=True,
    ))
    def get_order_status(self, obj):
        if obj.sandbox:
            return None
        user = self.context["request"].user
        if not user.is_authenticated or obj.status != "active":
            return None
        current_phase = obj.current_phase
        if current_phase is None:
            return None
        for phase_state in current_phase.phase_states.all():
            if phase_state.member.user_id == user.id:
                if phase_state.orders_confirmed:
                    return "orders_submitted"
                if not phase_state.has_possible_orders:
                    return "no_orders_required"
                if _phase_state_order_count(phase_state) == 0:
                    return "orders_required"
                if obj.deadline_mode == DeadlineMode.FIXED_TIME:
                    return "orders_submitted"
                return "orders_not_confirmed"
        return None

    @extend_schema_field(serializers.ListField(
        child=serializers.ChoiceField(choices=["nmr", "civil_disorder"]),
        allow_null=True,
    ))
    def get_member_status(self, obj):
        if obj.sandbox:
            return None
        user = self.context["request"].user
        if not user.is_authenticated:
            return []
        current_member = next(
            (m for m in obj.members.all() if m.user_id == user.id), None
        )
        if current_member is None:
            return []
        statuses = []
        if current_member.civil_disorder:
            statuses.append("civil_disorder")
        phases = list(obj.phases.all())
        completed_phases = [p for p in phases if p.status == "completed"]
        if completed_phases:
            prev_phase = max(completed_phases, key=lambda p: p.ordinal)
            for phase_state in prev_phase.phase_states.all():
                if phase_state.member.user_id == user.id:
                    if phase_state.orders_outcome == "nmr":
                        statuses.append("nmr")
                    break
        return statuses

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
    anonymous = serializers.BooleanField(default=False)
    game_master = serializers.BooleanField(default=False)
    deadline_mode = serializers.ChoiceField(
        choices=DeadlineMode.DEADLINE_MODE_CHOICES,
        default=DeadlineMode.FIXED_TIME,
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
    press_type = serializers.ChoiceField(
        choices=PressType.PRESS_TYPE_CHOICES,
        default=PressType.FULL_PRESS,
    )
    min_reliability = serializers.ChoiceField(
        choices=MinReliability.MIN_RELIABILITY_CHOICES,
        default=MinReliability.OPEN,
    )
    commitment_requirement = serializers.ChoiceField(
        choices=CommitmentRequirement.COMMITMENT_REQUIREMENT_CHOICES,
        default=CommitmentRequirement.OPEN,
    )
    def validate_variant_id(self, value):
        try:
            self._validated_variant = Variant.objects.get(
                id=value,
                status__in=[VariantStatus.PUBLISHED, VariantStatus.DRAFT],
            )
        except Variant.DoesNotExist:
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
        variant = self._validated_variant
        if variant.status == VariantStatus.DRAFT:
            request = self.context["request"]
            if not attrs.get("private"):
                raise serializers.ValidationError(
                    {"variant_id": "Draft variants can only be used for private games."}
                )
            if variant.owner_id is None or variant.owner_id != request.user.id:
                raise serializers.ValidationError(
                    {"variant_id": "You can only create games with your own draft variants."}
                )

        if attrs.get("game_master") and not attrs.get("private"):
            raise serializers.ValidationError(
                {"game_master": "A Game Master is only available in private games."}
            )

        if not attrs.get("game_master"):
            request = self.context["request"]
            commitment = request.user.profile.commitment
            if commitment == Commitment.LOW:
                raise serializers.ValidationError(
                    {"commitment_requirement": "Your commitment rating does not allow creating games."}
                )
            if (
                attrs["commitment_requirement"] == CommitmentRequirement.COMMITTED
                and commitment != Commitment.HIGH
            ):
                raise serializers.ValidationError(
                    {"commitment_requirement": "Only players with high commitment can require committed players."}
                )

        deadline_mode = attrs["deadline_mode"]

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
            attrs["movement_phase_duration"] = None
            attrs["retreat_phase_duration"] = None
        else:
            attrs["fixed_deadline_time"] = None
            attrs["fixed_deadline_timezone"] = None
            attrs["movement_frequency"] = None
            attrs["retreat_frequency"] = None

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        variant = Variant.objects.with_game_creation_data().get(id=validated_data["variant_id"])

        with_game_master = validated_data["game_master"]

        with transaction.atomic():
            game = Game.objects.create_from_template(
                variant,
                name=validated_data["name"],
                created_by=request.user,
                game_master=request.user if with_game_master else None,
                admin=request.user,
                nation_assignment=validated_data["nation_assignment"],
                movement_phase_duration=validated_data["movement_phase_duration"],
                retreat_phase_duration=validated_data.get("retreat_phase_duration"),
                private=validated_data["private"],
                anonymous=validated_data["anonymous"],
                deadline_mode=validated_data["deadline_mode"],
                fixed_deadline_time=validated_data.get("fixed_deadline_time"),
                fixed_deadline_timezone=validated_data.get("fixed_deadline_timezone"),
                movement_frequency=validated_data.get("movement_frequency"),
                retreat_frequency=validated_data.get("retreat_frequency"),
                nmr_extensions_allowed=validated_data["nmr_extensions_allowed"],
                press_type=validated_data["press_type"],
                min_reliability=validated_data["min_reliability"],
                commitment_requirement=validated_data["commitment_requirement"],
            )

            public_channel = game.channels.create(name="Public Press", private=False)
            if not with_game_master:
                creator_member = game.members.create(user=request.user)
                public_channel.member_channels.create(member=creator_member)

            game.start_if_full()

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

        game = Game.objects.create_sandbox(
            user=request.user,
            name=validated_data["name"],
            variant=variant,
        )

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

            nations_list = [n for n in source_game.variant.nations.all() if not n.non_playable]
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
        actor = self.context["request"].user
        instance.pause()
        emit("game_paused", game=instance, actor=actor)
        return instance

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data


class GameUnpauseSerializer(serializers.Serializer):
    def validate(self, attrs):
        if not self.instance.is_paused:
            raise serializers.ValidationError("Game is not paused")
        return attrs

    def update(self, instance, validated_data):
        actor = self.context["request"].user
        instance.unpause()
        emit("game_resumed", game=instance, actor=actor)
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
        actor = self.context["request"].user
        instance.extend_deadline(validated_data["duration"])
        emit("game_deadline_extended", game=instance, actor=actor)
        return instance

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data
