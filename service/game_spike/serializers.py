from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from common.constants import (
    ActionBlockedReason,
    Commitment,
    CommitmentBand,
    CommitmentEligibility,
    CommitmentRequirement,
    DeadlineMode,
    GameActionKey,
    MemberDeparture,
    MemberStatus,
    MovementPhaseDuration,
    MusterStatus,
    MyGameResult,
    MyGamesSection,
    MyGameStateKind,
    OrderStatus,
    PhaseFrequency,
    PressType,
    VariantStatus,
)
from common.fields import ActionsField, ViewerField
from common.serializers import OutputListSerializer, OutputSerializer, queries_disabled
from nation.models import Nation
from province.models import Province
from variant.models import Variant

from .loaders import GameListLoader, GameRetrieveLoader, MyGameLoader
from .models import Game, Member, Phase, SupplyCenter, Unit, Victory

User = get_user_model()


class GameMasterSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="id", read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)
    picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("user_id", "name", "picture")

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_picture(self, user):
        return user.profile.picture_url(self.context["request"])


class MemberSerializer(serializers.ModelSerializer):
    user_id = ViewerField(serializers.IntegerField(allow_null=True), source="visible_user_id")
    name = ViewerField(serializers.CharField(), source="visible_name")
    picture = serializers.SerializerMethodField()
    is_current_user = ViewerField(serializers.BooleanField(), anonymous=False)
    is_bot = serializers.BooleanField(read_only=True)
    commitment = ViewerField(serializers.CharField(allow_null=True), source="visible_commitment")
    nation = serializers.CharField(source="nation.name", read_only=True, allow_null=True)
    kicked = serializers.BooleanField(source="left_seat", read_only=True)
    is_game_creator = ViewerField(serializers.BooleanField())
    is_admin = ViewerField(serializers.BooleanField())
    eliminated = serializers.BooleanField(read_only=True)
    civil_disorder = serializers.BooleanField(read_only=True)
    withdrawn = serializers.BooleanField(read_only=True)
    replaceable = serializers.BooleanField(read_only=True)
    seat_confirmed = serializers.BooleanField(read_only=True, allow_null=True)
    removable = serializers.BooleanField(read_only=True)
    nation_preference_ids = ViewerField(
        serializers.ListField(child=serializers.CharField()), source="visible_nation_preference_ids"
    )
    commitment_total = ViewerField(serializers.IntegerField(allow_null=True), source="visible_commitment_total")
    commitment_band = ViewerField(
        serializers.ChoiceField(choices=CommitmentBand.BAND_CHOICES, allow_null=True), source="visible_commitment_band"
    )

    class Meta:
        model = Member
        fields = (
            "id",
            "user_id",
            "name",
            "picture",
            "is_current_user",
            "is_bot",
            "commitment",
            "nation",
            "eliminated",
            "kicked",
            "is_game_creator",
            "is_admin",
            "nmr_extensions_remaining",
            "civil_disorder",
            "withdrawn",
            "seeking_replacement",
            "replaceable",
            "seat_confirmed",
            "removable",
            "nation_preference_ids",
            "commitment_total",
            "commitment_band",
        )

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_picture(self, member):
        request = self.context["request"]
        if member.is_masked_for(request.user) or member.user is None:
            return None
        return member.user.profile.picture_url(request)


class VictorySerializer(serializers.ModelSerializer):
    type = serializers.CharField(read_only=True)
    winning_phase_id = serializers.IntegerField(read_only=True)
    members = MemberSerializer(source="winners", many=True, read_only=True)

    class Meta:
        model = Victory
        fields = ("id", "type", "winning_phase_id", "members")


class BoardNationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nation
        fields = ("name",)


class BoardProvinceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="province_id", read_only=True)

    class Meta:
        model = Province
        fields = ("id",)


class GameListUnitSerializer(serializers.ModelSerializer):
    nation = BoardNationSerializer(read_only=True)
    province = BoardProvinceSerializer(read_only=True)

    class Meta:
        model = Unit
        fields = ("type", "nation", "province", "dislodged")


class GameListSupplyCenterSerializer(serializers.ModelSerializer):
    nation = BoardNationSerializer(read_only=True)
    province = BoardProvinceSerializer(read_only=True)

    class Meta:
        model = SupplyCenter
        fields = ("nation", "province")


class GameListCurrentPhaseSerializer(serializers.ModelSerializer):
    remaining_time = serializers.IntegerField(source="remaining_time_seconds", read_only=True, allow_null=True)
    units = GameListUnitSerializer(many=True, read_only=True)
    supply_centers = GameListSupplyCenterSerializer(many=True, read_only=True)

    class Meta:
        model = Phase
        fields = (
            "id",
            "ordinal",
            "season",
            "year",
            "name",
            "type",
            "status",
            "scheduled_resolution",
            "remaining_time",
            "units",
            "supply_centers",
        )


class GameActionSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=GameActionKey.KEY_CHOICES, read_only=True)
    blocked_reason = serializers.ChoiceField(
        choices=ActionBlockedReason.REASON_CHOICES, allow_null=True, read_only=True
    )


class GameSerializer(OutputSerializer):
    can_join = ViewerField(serializers.BooleanField(), anonymous=False)
    can_leave = ViewerField(serializers.BooleanField(), anonymous=False)
    can_withdraw = ViewerField(serializers.BooleanField(), anonymous=False)
    can_delete = ViewerField(serializers.BooleanField(), anonymous=False)
    can_manage = ViewerField(serializers.BooleanField(), anonymous=False)
    game_master = GameMasterSerializer(read_only=True, allow_null=True)
    variant_id = serializers.CharField(read_only=True)
    phases = serializers.ListField(child=serializers.IntegerField(), source="phase_ids", read_only=True)
    current_phase_id = serializers.IntegerField(read_only=True, allow_null=True)
    phase_confirmed = ViewerField(serializers.BooleanField(), anonymous=False)
    order_status = ViewerField(
        serializers.ChoiceField(choices=OrderStatus.STATUS_CHOICES, allow_null=True), anonymous=None
    )
    member_status = ViewerField(
        serializers.ListField(child=serializers.ChoiceField(choices=MemberStatus.STATUS_CHOICES), allow_null=True)
    )
    show_short_game_join_warning = serializers.BooleanField(read_only=True)
    members = MemberSerializer(source="players", many=True, read_only=True)
    victory = VictorySerializer(read_only=True, allow_null=True)
    is_paused = serializers.BooleanField(read_only=True)
    commitment_eligibility = ViewerField(
        serializers.ChoiceField(
            choices=(
                CommitmentEligibility.ELIGIBLE,
                CommitmentEligibility.COMMITTED_LOCKED,
                CommitmentEligibility.LOW_LOCKED,
            ),
            allow_null=True,
        )
    )
    muster_status = ViewerField(
        serializers.ChoiceField(choices=(MusterStatus.CONFIRMATION_REQUIRED, MusterStatus.CONFIRMED), allow_null=True),
        anonymous=None,
    )
    total_unread_message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Game
        fields = (
            "id",
            "name",
            "status",
            "created_at",
            "can_join",
            "can_leave",
            "can_withdraw",
            "can_delete",
            "can_manage",
            "game_master",
            "variant_id",
            "phases",
            "current_phase_id",
            "phase_confirmed",
            "order_status",
            "member_status",
            "private",
            "anonymous",
            "movement_phase_duration",
            "retreat_phase_duration",
            "show_short_game_join_warning",
            "members",
            "victory",
            "sandbox",
            "is_paused",
            "paused_at",
            "nmr_extensions_allowed",
            "deadline_mode",
            "fixed_deadline_time",
            "fixed_deadline_timezone",
            "movement_frequency",
            "retreat_frequency",
            "press_type",
            "commitment_requirement",
            "commitment_eligibility",
            "muster_required",
            "muster_deadline",
            "muster_status",
            "total_unread_message_count",
        )


class GameListSerializer(GameSerializer):
    loader = GameListLoader
    current_phase = GameListCurrentPhaseSerializer(read_only=True, allow_null=True)

    class Meta(GameSerializer.Meta):
        fields = GameSerializer.Meta.fields + ("current_phase",)


class GameRetrieveSerializer(GameSerializer):
    loader = GameRetrieveLoader
    can_create_channel = ViewerField(serializers.BooleanField(), anonymous=False)
    game_master_member_id = serializers.IntegerField(read_only=True, allow_null=True)
    actions = ActionsField(GameActionKey.GAME_INFO_KEYS, GameActionSerializer)
    player_list_actions = ActionsField(GameActionKey.PLAYER_LIST_KEYS, GameActionSerializer)

    class Meta(GameSerializer.Meta):
        fields = GameSerializer.Meta.fields + (
            "can_create_channel",
            "game_master_member_id",
            "actions",
            "player_list_actions",
        )


class MyGameStateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=MyGameStateKind.KIND_CHOICES, read_only=True)
    deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    result = serializers.ChoiceField(choices=MyGameResult.RESULT_CHOICES, read_only=True, allow_null=True)
    winner = serializers.CharField(read_only=True, allow_null=True)
    departure = serializers.ChoiceField(choices=MemberDeparture.DEPARTURE_CHOICES, read_only=True, allow_null=True)


class MyGameSeatsSerializer(serializers.Serializer):
    filled = serializers.IntegerField(read_only=True)
    total = serializers.IntegerField(read_only=True)


class MyGameSerializer(OutputSerializer):
    loader = MyGameLoader
    variant_id = serializers.CharField(read_only=True)
    current_phase_id = serializers.IntegerField(read_only=True, allow_null=True)
    current_phase = GameListCurrentPhaseSerializer(read_only=True, allow_null=True)
    nation = ViewerField(serializers.CharField(allow_null=True), source="seat_nation")
    seats = MyGameSeatsSerializer(source="seat_counts", read_only=True, allow_null=True)
    unread_count = serializers.IntegerField(source="total_unread_message_count", read_only=True)
    state = ViewerField(MyGameStateSerializer(), source="my_state")

    class Meta:
        model = Game
        fields = (
            "id",
            "name",
            "status",
            "variant_id",
            "sandbox",
            "current_phase_id",
            "current_phase",
            "nation",
            "seats",
            "unread_count",
            "state",
        )


class MyGamesCurrentListSerializer(OutputListSerializer):
    def to_representation(self, games):
        user = self.context["request"].user
        sections = {}
        for game in sorted(games, key=lambda game: game.my_sort_key(user)):
            sections.setdefault(game.my_section(user), []).append(self.child.to_representation(game))
        return {
            "sections": [
                {"key": key, "games": sections[key]} for key, _ in MyGamesSection.SECTION_CHOICES if key in sections
            ]
        }

    @property
    def data(self):
        with queries_disabled():
            return ReturnDict(self.to_representation(self.instance), serializer=self)


class MyGamesCurrentSerializer(MyGameSerializer):
    class Meta(MyGameSerializer.Meta):
        list_serializer_class = MyGamesCurrentListSerializer


class GameCreateSerializer(serializers.ModelSerializer):
    variant_id = serializers.CharField()
    game_master = serializers.BooleanField(default=False)
    movement_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
        default=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )
    retreat_phase_duration = serializers.ChoiceField(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES, required=False, allow_null=True, default=None
    )
    private = serializers.BooleanField()
    anonymous = serializers.BooleanField(default=False)
    deadline_mode = serializers.ChoiceField(choices=DeadlineMode.DEADLINE_MODE_CHOICES, default=DeadlineMode.FIXED_TIME)
    fixed_deadline_time = serializers.TimeField(required=False, allow_null=True, default=None)
    fixed_deadline_timezone = serializers.CharField(required=False, allow_null=True, default=None, max_length=50)
    movement_frequency = serializers.ChoiceField(
        choices=PhaseFrequency.PHASE_FREQUENCY_CHOICES, required=False, allow_null=True, default=None
    )
    retreat_frequency = serializers.ChoiceField(
        choices=PhaseFrequency.PHASE_FREQUENCY_CHOICES, required=False, allow_null=True, default=None
    )
    nmr_extensions_allowed = serializers.IntegerField(required=False, default=0, min_value=0, max_value=2)
    press_type = serializers.ChoiceField(choices=PressType.PRESS_TYPE_CHOICES, default=PressType.FULL_PRESS)
    commitment_requirement = serializers.ChoiceField(
        choices=CommitmentRequirement.COMMITMENT_REQUIREMENT_CHOICES, default=CommitmentRequirement.OPEN
    )
    muster_required = serializers.BooleanField(default=False)

    class Meta:
        model = Game
        fields = (
            "name",
            "variant_id",
            "game_master",
            "movement_phase_duration",
            "retreat_phase_duration",
            "private",
            "anonymous",
            "deadline_mode",
            "fixed_deadline_time",
            "fixed_deadline_timezone",
            "movement_frequency",
            "retreat_frequency",
            "nmr_extensions_allowed",
            "press_type",
            "commitment_requirement",
            "muster_required",
        )

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value, status__in=(VariantStatus.PUBLISHED, VariantStatus.DRAFT)).exists():
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
        user = self.context["request"].user
        variant = Variant.objects.get(id=attrs["variant_id"])
        if variant.status == VariantStatus.DRAFT:
            if not attrs["private"]:
                raise serializers.ValidationError({"variant_id": "Draft variants can only be used for private games."})
            if variant.owner_id != user.id:
                raise serializers.ValidationError(
                    {"variant_id": "You can only create games with your own draft variants."}
                )
        if attrs["game_master"] and not attrs["private"]:
            raise serializers.ValidationError({"game_master": "A Game Master is only available in private games."})
        if not attrs["game_master"]:
            commitment = user.profile.commitment
            if commitment == Commitment.LOW and not attrs["private"]:
                raise serializers.ValidationError(
                    {"commitment_requirement": "Your commitment rating does not allow creating public games."}
                )
            if attrs["commitment_requirement"] == CommitmentRequirement.COMMITTED and commitment != Commitment.HIGH:
                raise serializers.ValidationError(
                    {"commitment_requirement": "Only players with high commitment can require committed players."}
                )
        if attrs["deadline_mode"] == DeadlineMode.FIXED_TIME:
            for field in ("fixed_deadline_time", "fixed_deadline_timezone", "movement_frequency"):
                if not attrs.get(field):
                    raise serializers.ValidationError({field: "Required when deadline_mode is 'fixed_time'."})
            attrs["movement_phase_duration"] = None
            attrs["retreat_phase_duration"] = None
        else:
            attrs["fixed_deadline_time"] = None
            attrs["fixed_deadline_timezone"] = None
            attrs["movement_frequency"] = None
            attrs["retreat_frequency"] = None
            if not attrs["private"]:
                errors = {
                    field: "Short phase durations are only available in private games."
                    for field in ("movement_phase_duration", "retreat_phase_duration")
                    if attrs.get(field) in MovementPhaseDuration.PRIVATE_ONLY_DURATIONS
                }
                if errors:
                    raise serializers.ValidationError(errors)
        return attrs


class GameCreateSandboxSerializer(serializers.ModelSerializer):
    variant_id = serializers.CharField()

    class Meta:
        model = Game
        fields = ("name", "variant_id")

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Variant with this ID does not exist.")
        return value


class GameExtendDeadlineSerializer(serializers.Serializer):
    duration = serializers.ChoiceField(choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES)
