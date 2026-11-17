from zoneinfo import ZoneInfo

from rest_framework import serializers
from django.db import transaction
from common.constants import (
    ActionBlockedReason,
    CommitmentRequirement,
    DeadlineMode,
    GameActionKey,
    MemberDeparture,
    MemberKind,
    MovementPhaseDuration,
    MusterStatus,
    MyGameResult,
    MyGamesSection,
    MyGameStateKind,
    PhaseFrequency,
    PhaseStatus,
    PressType,
    VariantStatus,
)
from member.serializers import MemberSerializer
from common.serializers import AbsoluteUrlField, derived, hydrated
from emit import emit

from victory.serializers import VictorySerializer
from variant.models import Variant
from common.policies import Refused
from member.checks import MeetsCommitmentRequirementCheck
from member.models import Member
from rating.policies import RankablePolicy
from .loaders import GameListLoader, GameRetrieveLoader
from .models import Game


class GameMasterSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="id", read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)
    picture = AbsoluteUrlField(source="profile.picture_path")


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
    remaining_time = serializers.IntegerField(
        source="remaining_time_seconds", read_only=True
    )
    units = hydrated(
        GameListUnitSerializer(many=True, read_only=True, source="board_units")
    )
    supply_centers = hydrated(
        GameListSupplyCenterSerializer(
            many=True, read_only=True, source="board_supply_centers"
        )
    )


class GameListSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    can_join = hydrated(
        serializers.BooleanField(source="viewer_can_join", read_only=True)
    )
    can_leave = hydrated(
        serializers.BooleanField(source="viewer_can_leave", read_only=True)
    )
    can_withdraw = hydrated(
        serializers.BooleanField(source="viewer_can_withdraw", read_only=True)
    )
    can_delete = hydrated(
        serializers.BooleanField(source="viewer_can_delete", read_only=True)
    )
    can_manage = hydrated(
        serializers.BooleanField(source="viewer_can_manage", read_only=True)
    )
    game_master = GameMasterSerializer(allow_null=True, read_only=True)
    variant_id = serializers.CharField(source="variant.id", read_only=True)
    phases = serializers.ListField(
        child=serializers.IntegerField(), source="phase_ids", read_only=True
    )
    current_phase_id = derived(
        serializers.IntegerField(
            source="current_phase.id", read_only=True, allow_null=True
        )
    )
    current_phase = derived(
        GameListCurrentPhaseSerializer(read_only=True, allow_null=True)
    )
    phase_confirmed = hydrated(
        serializers.BooleanField(source="viewer_phase_confirmed", read_only=True)
    )
    order_status = hydrated(
        serializers.ChoiceField(
            source="viewer_order_status",
            choices=[
                "orders_required",
                "orders_submitted",
                "orders_not_confirmed",
                "no_orders_required",
            ],
            read_only=True,
            allow_null=True,
        )
    )
    member_status = hydrated(
        serializers.ListField(
            source="viewer_member_status",
            child=serializers.ChoiceField(choices=["nmr", "civil_disorder"]),
            read_only=True,
            allow_null=True,
        )
    )
    private = serializers.BooleanField(read_only=True)
    anonymous = serializers.BooleanField(read_only=True)
    ranked = serializers.BooleanField(read_only=True)
    movement_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    retreat_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    show_short_game_join_warning = serializers.BooleanField(read_only=True)
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
    commitment_requirement = serializers.CharField(read_only=True)
    join_blocked_reason = hydrated(
        serializers.ChoiceField(
            source="viewer_join_blocked_reason",
            choices=ActionBlockedReason.REASON_CHOICES,
            read_only=True,
            allow_null=True,
        )
    )
    muster_required = serializers.BooleanField(read_only=True)
    muster_deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    muster_status = hydrated(
        serializers.ChoiceField(
            source="viewer_muster_status",
            choices=[MusterStatus.CONFIRMATION_REQUIRED, MusterStatus.CONFIRMED],
            read_only=True,
            allow_null=True,
        )
    )
    total_unread_message_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        loader = GameListLoader


class MyGameStateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=MyGameStateKind.KIND_CHOICES, read_only=True)
    deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    result = serializers.ChoiceField(
        choices=MyGameResult.RESULT_CHOICES, read_only=True, allow_null=True
    )
    winner = serializers.CharField(read_only=True, allow_null=True)
    departure = serializers.ChoiceField(
        choices=MemberDeparture.DEPARTURE_CHOICES, read_only=True, allow_null=True
    )


class MyGameSeatsSerializer(serializers.Serializer):
    filled = serializers.IntegerField(read_only=True)
    total = serializers.IntegerField(read_only=True)


class MyGameSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    variant_id = serializers.CharField(read_only=True)
    sandbox = serializers.BooleanField(read_only=True)
    current_phase_id = serializers.IntegerField(read_only=True, allow_null=True)
    current_phase = GameListCurrentPhaseSerializer(read_only=True, allow_null=True)
    nation = serializers.CharField(read_only=True, allow_null=True)
    seats = MyGameSeatsSerializer(read_only=True, allow_null=True)
    unread_count = serializers.IntegerField(read_only=True)
    state = MyGameStateSerializer(read_only=True)


class MyGamesSectionSerializer(serializers.Serializer):
    key = serializers.ChoiceField(
        choices=MyGamesSection.SECTION_CHOICES, read_only=True
    )
    games = MyGameSerializer(many=True, read_only=True)


class MyGamesCurrentSerializer(serializers.Serializer):
    sections = MyGamesSectionSerializer(many=True, read_only=True)


class GameFindSimilarSerializer(serializers.Serializer):
    game = GameListSerializer(allow_null=True)


class GameFastestSerializer(serializers.Serializer):
    game = GameListSerializer(allow_null=True)


class GameActionSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=GameActionKey.KEY_CHOICES, read_only=True)
    blocked_reason = serializers.ChoiceField(
        choices=ActionBlockedReason.REASON_CHOICES, allow_null=True, read_only=True
    )


class GameRetrieveSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    can_join = hydrated(
        serializers.BooleanField(source="viewer_can_join", read_only=True)
    )
    can_leave = hydrated(
        serializers.BooleanField(source="viewer_can_leave", read_only=True)
    )
    can_withdraw = hydrated(
        serializers.BooleanField(source="viewer_can_withdraw", read_only=True)
    )
    is_first_year = serializers.BooleanField(source="in_first_year", read_only=True)
    can_delete = hydrated(
        serializers.BooleanField(source="viewer_can_delete", read_only=True)
    )
    can_manage = hydrated(
        serializers.BooleanField(source="viewer_can_manage", read_only=True)
    )
    can_create_channel = hydrated(
        serializers.BooleanField(source="viewer_can_create_channel", read_only=True)
    )
    game_master = GameMasterSerializer(allow_null=True, read_only=True)
    game_master_member_id = derived(
        serializers.IntegerField(read_only=True, allow_null=True)
    )
    phases = derived(
        serializers.ListField(
            child=serializers.IntegerField(), source="phase_ids", read_only=True
        )
    )
    current_phase_id = derived(
        serializers.IntegerField(
            source="current_phase.id", read_only=True, allow_null=True
        )
    )
    members = MemberSerializer(many=True, read_only=True)
    sandbox = serializers.BooleanField(read_only=True)
    victory = VictorySerializer(read_only=True, allow_null=True)
    variant_id = serializers.CharField(source="variant.id", read_only=True)
    phase_confirmed = hydrated(
        serializers.BooleanField(source="viewer_phase_confirmed", read_only=True)
    )
    order_status = hydrated(
        serializers.ChoiceField(
            source="viewer_order_status",
            choices=[
                "orders_required",
                "orders_submitted",
                "orders_not_confirmed",
                "no_orders_required",
            ],
            read_only=True,
            allow_null=True,
        )
    )
    member_status = hydrated(
        serializers.ListField(
            source="viewer_member_status",
            child=serializers.ChoiceField(choices=["nmr", "civil_disorder"]),
            read_only=True,
            allow_null=True,
        )
    )
    movement_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    retreat_phase_duration = serializers.CharField(read_only=True, allow_null=True)
    show_short_game_join_warning = serializers.BooleanField(read_only=True)
    private = serializers.BooleanField(read_only=True)
    anonymous = serializers.BooleanField(read_only=True)
    ranked = serializers.BooleanField(read_only=True)
    is_paused = serializers.BooleanField(read_only=True)
    paused_at = serializers.DateTimeField(read_only=True, allow_null=True)
    nmr_extensions_allowed = serializers.IntegerField(read_only=True)
    deadline_mode = serializers.CharField(read_only=True)
    fixed_deadline_time = serializers.TimeField(read_only=True, allow_null=True)
    fixed_deadline_timezone = serializers.CharField(read_only=True, allow_null=True)
    movement_frequency = serializers.CharField(read_only=True, allow_null=True)
    retreat_frequency = serializers.CharField(read_only=True, allow_null=True)
    press_type = serializers.CharField(read_only=True)
    commitment_requirement = serializers.CharField(read_only=True)
    join_blocked_reason = hydrated(
        serializers.ChoiceField(
            source="viewer_join_blocked_reason",
            choices=ActionBlockedReason.REASON_CHOICES,
            read_only=True,
            allow_null=True,
        )
    )
    muster_required = serializers.BooleanField(read_only=True)
    muster_deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    muster_status = hydrated(
        serializers.ChoiceField(
            source="viewer_muster_status",
            choices=[MusterStatus.CONFIRMATION_REQUIRED, MusterStatus.CONFIRMED],
            read_only=True,
            allow_null=True,
        )
    )
    total_unread_message_count = hydrated(serializers.IntegerField(read_only=True))
    actions = hydrated(
        GameActionSerializer(many=True, read_only=True, source="viewer_actions")
    )
    player_list_actions = hydrated(
        GameActionSerializer(
            many=True, read_only=True, source="viewer_player_list_actions"
        )
    )

    class Meta:
        loader = GameRetrieveLoader


class GameCreateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    variant_id = serializers.CharField()
    movement_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
        default=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )
    retreat_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
        required=False,
        allow_null=True,
        default=None,
    )
    private = serializers.BooleanField()
    anonymous = serializers.BooleanField(default=False)
    ranked = serializers.BooleanField(default=False)
    game_master = serializers.BooleanField(default=False)
    deadline_mode = serializers.ChoiceField(
        choices=DeadlineMode.DEADLINE_MODE_CHOICES,
        default=DeadlineMode.FIXED_TIME,
    )
    fixed_deadline_time = serializers.TimeField(
        required=False, allow_null=True, default=None
    )
    fixed_deadline_timezone = serializers.CharField(
        required=False, allow_null=True, default=None, max_length=50
    )
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
                    {
                        "variant_id": "You can only create games with your own draft variants."
                    }
                )

        if attrs.get("game_master") and not attrs.get("private"):
            raise serializers.ValidationError(
                {"game_master": "A Game Master is only available in private games."}
            )

        if not attrs.get("game_master"):
            decision = MeetsCommitmentRequirementCheck.decide(
                Game(commitment_requirement=attrs["commitment_requirement"]),
                self.context["request"].user,
            )
            if not decision:
                raise Refused(decision)

        if attrs["ranked"]:
            decision = RankablePolicy.decide(
                Game(variant=variant, private=attrs["private"]),
                self.context["request"].user,
            )
            if not decision:
                raise Refused(decision)

        deadline_mode = attrs["deadline_mode"]

        if deadline_mode == DeadlineMode.FIXED_TIME:
            if not attrs.get("fixed_deadline_time"):
                raise serializers.ValidationError(
                    {
                        "fixed_deadline_time": "Required when deadline_mode is 'fixed_time'."
                    }
                )
            if not attrs.get("fixed_deadline_timezone"):
                raise serializers.ValidationError(
                    {
                        "fixed_deadline_timezone": "Required when deadline_mode is 'fixed_time'."
                    }
                )
            if not attrs.get("movement_frequency"):
                raise serializers.ValidationError(
                    {
                        "movement_frequency": "Required when deadline_mode is 'fixed_time'."
                    }
                )
            attrs["movement_phase_duration"] = None
            attrs["retreat_phase_duration"] = None
        else:
            attrs["fixed_deadline_time"] = None
            attrs["fixed_deadline_timezone"] = None
            attrs["movement_frequency"] = None
            attrs["retreat_frequency"] = None
            if not attrs.get("private"):
                private_only_error = (
                    "Short phase durations are only available in private games."
                )
                errors = {}
                if (
                    attrs.get("movement_phase_duration")
                    in MovementPhaseDuration.PRIVATE_ONLY_DURATIONS
                ):
                    errors["movement_phase_duration"] = private_only_error
                if (
                    attrs.get("retreat_phase_duration")
                    in MovementPhaseDuration.PRIVATE_ONLY_DURATIONS
                ):
                    errors["retreat_phase_duration"] = private_only_error
                if errors:
                    raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        variant = Variant.objects.with_game_creation_data().get(
            id=validated_data["variant_id"]
        )

        with_game_master = validated_data["game_master"]

        with transaction.atomic():
            game = Game.objects.create_from_template(
                variant,
                name=validated_data["name"],
                created_by=request.user,
                game_master=request.user if with_game_master else None,
                admin=request.user,
                movement_phase_duration=validated_data["movement_phase_duration"],
                retreat_phase_duration=validated_data.get("retreat_phase_duration"),
                private=validated_data["private"],
                anonymous=validated_data["anonymous"],
                ranked=validated_data["ranked"],
                deadline_mode=validated_data["deadline_mode"],
                fixed_deadline_time=validated_data.get("fixed_deadline_time"),
                fixed_deadline_timezone=validated_data.get("fixed_deadline_timezone"),
                movement_frequency=validated_data.get("movement_frequency"),
                retreat_frequency=validated_data.get("retreat_frequency"),
                nmr_extensions_allowed=validated_data["nmr_extensions_allowed"],
                press_type=validated_data["press_type"],
                commitment_requirement=validated_data["commitment_requirement"],
                muster_required=not validated_data["private"],
            )

            public_channel = game.channels.create(name="Public Press", private=False)
            creator_member = game.members.create(
                user=request.user,
                kind=MemberKind.GAME_MASTER if with_game_master else MemberKind.PLAYER,
            )
            public_channel.member_channels.create(member=creator_member)

            game.start_if_full()

            if hasattr(game, "_created_phase"):
                delattr(game, "_created_phase")

        return GameRetrieveLoader.get(game.id, request.user)

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
        variant = Variant.objects.with_game_creation_data().get(
            id=validated_data["variant_id"]
        )

        game = Game.objects.create_sandbox(
            user=request.user,
            name=validated_data["name"],
            variant=variant,
        )

        return GameRetrieveLoader.get(game.id, request.user)

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
            user_sandboxes = (
                Game.objects.filter(sandbox=True, members__user=user)
                .distinct()
                .order_by("created_at")
            )

            if user_sandboxes.count() >= 3:
                oldest_sandbox = user_sandboxes.first()
                oldest_sandbox.delete()

            game = Game.objects.clone_from_phase(
                source_phase,
                name=f"{source_game.name} (Sandbox)",
            )

            nations_list = [
                n for n in source_game.variant.nations.all() if not n.non_playable
            ]
            members_to_create = [
                Member(game=game, user=user, sandbox=True) for _ in nations_list
            ]
            created_members = Member.objects.bulk_create(members_to_create)

            game.start(current_phase=game._created_phase, members=created_members)

        return GameRetrieveLoader.get(game.id, request.user)

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
        return GameRetrieveLoader.get(instance.id, actor)

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
        return GameRetrieveLoader.get(instance.id, actor)

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
            raise serializers.ValidationError(
                "Cannot extend deadline while game is paused"
            )
        current_phase = self.instance.current_phase
        if not current_phase or not current_phase.scheduled_resolution:
            raise serializers.ValidationError(
                "No active phase with a scheduled resolution"
            )
        return attrs

    def update(self, instance, validated_data):
        actor = self.context["request"].user
        instance.extend_deadline(validated_data["duration"])
        emit("game_deadline_extended", game=instance, actor=actor)
        return GameRetrieveLoader.get(instance.id, actor)

    def to_representation(self, instance):
        return GameRetrieveSerializer(instance, context=self.context).data
