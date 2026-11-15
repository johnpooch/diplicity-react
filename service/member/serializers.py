from rest_framework import serializers
from django.db import IntegrityError, transaction

from common.constants import (
    ActionBlockedReason,
    CommitmentBand,
    GameActionKey,
    MemberActionKey,
    ParticipationStatus,
    WithdrawalReason,
)
from common.serializers import AbsoluteUrlField, derived, hydrated
from bot.constants import BotKind
from emit import emit
from user_profile.models import UserProfile

from .loaders import BaseMemberLoader, MemberDetailLoader, MemberLoader
from .models import Member


class BaseMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = hydrated(
        serializers.IntegerField(
            source="visible_user_id", read_only=True, allow_null=True
        )
    )
    name = hydrated(serializers.CharField(source="visible_name", read_only=True))
    picture = hydrated(AbsoluteUrlField(source="visible_picture_path"))
    is_current_user = hydrated(serializers.BooleanField(read_only=True))
    is_bot = serializers.BooleanField(read_only=True)
    bot_kind = derived(
        serializers.ChoiceField(
            source="user.bot.kind",
            choices=BotKind.KIND_CHOICES,
            read_only=True,
            allow_null=True,
        )
    )

    class Meta:
        loader = BaseMemberLoader


class MemberSerializer(BaseMemberSerializer):
    nation = serializers.CharField(
        allow_null=True, read_only=True, source="nation.name"
    )
    eliminated = serializers.BooleanField(read_only=True)
    kicked = serializers.BooleanField(read_only=True, source="left_seat")
    is_game_creator = hydrated(
        serializers.BooleanField(source="visible_is_game_creator", read_only=True)
    )
    is_admin = hydrated(
        serializers.BooleanField(source="visible_is_admin", read_only=True)
    )
    nmr_extensions_remaining = serializers.IntegerField(read_only=True)
    civil_disorder = serializers.BooleanField(read_only=True)
    withdrawn = serializers.BooleanField(read_only=True)
    seeking_replacement = serializers.BooleanField(read_only=True)
    replaceable = serializers.BooleanField(read_only=True)
    seat_confirmed = serializers.BooleanField(read_only=True, allow_null=True)
    removable = serializers.BooleanField(read_only=True)
    nation_preference_ids = hydrated(
        serializers.ListField(
            child=serializers.CharField(),
            source="visible_nation_preference_ids",
            read_only=True,
        )
    )
    commitment_total = hydrated(
        serializers.IntegerField(
            source="public_commitment_total", read_only=True, allow_null=True
        )
    )
    commitment_band = hydrated(
        serializers.ChoiceField(
            source="public_commitment_band",
            choices=CommitmentBand.BAND_CHOICES,
            read_only=True,
            allow_null=True,
        )
    )
    rating_change = derived(serializers.IntegerField(read_only=True, allow_null=True))
    rating_before = derived(serializers.IntegerField(read_only=True, allow_null=True))
    rating_after = derived(serializers.IntegerField(read_only=True, allow_null=True))

    class Meta:
        loader = MemberLoader


class MemberActionSerializer(serializers.Serializer):
    key = serializers.ChoiceField(
        choices=GameActionKey.KEY_CHOICES + MemberActionKey.KEY_CHOICES, read_only=True
    )
    blocked_reason = serializers.ChoiceField(
        choices=ActionBlockedReason.REASON_CHOICES, allow_null=True, read_only=True
    )


class MemberDetailSerializer(BaseMemberSerializer):
    is_admin = hydrated(
        serializers.BooleanField(source="visible_is_admin", read_only=True)
    )
    nation = serializers.CharField(
        allow_null=True, read_only=True, source="nation.name"
    )
    participation_status = serializers.ChoiceField(
        choices=ParticipationStatus.STATUS_CHOICES, read_only=True
    )
    supply_center_count = hydrated(
        serializers.IntegerField(read_only=True, allow_null=True)
    )
    unit_count = hydrated(serializers.IntegerField(read_only=True, allow_null=True))
    nmr_extensions_remaining = serializers.IntegerField(read_only=True)
    nmr_extensions_allowed = serializers.IntegerField(
        read_only=True, source="game.nmr_extensions_allowed"
    )
    nation_preferences = hydrated(
        serializers.ListField(
            child=serializers.CharField(),
            source="visible_nation_preferences",
            read_only=True,
            allow_null=True,
        )
    )
    actions = hydrated(
        MemberActionSerializer(many=True, read_only=True, source="viewer_actions")
    )
    can_report = hydrated(
        serializers.BooleanField(source="viewer_can_report", read_only=True)
    )
    already_reported = hydrated(
        serializers.BooleanField(source="viewer_already_reported", read_only=True)
    )
    rated = serializers.BooleanField(read_only=True)

    class Meta:
        loader = MemberDetailLoader


class MemberJoinSerializer(MemberSerializer):
    def create(self, validated_data):
        return self.context["game"].seat(self.context["request"].user)


class MemberWithdrawSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(
        choices=WithdrawalReason.REASON_CHOICES, required=False, write_only=True
    )

    def update(self, instance, validated_data):
        return Member.objects.withdraw(instance, validated_data.get("reason", ""))

    def to_representation(self, instance):
        return MemberSerializer(instance, context=self.context).data


class MemberCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(write_only=True)

    def _resolve_addable_user(self, user_id):
        profile = (
            UserProfile.objects.addable_to_game(self.context["game"])
            .filter(user_id=user_id)
            .first()
        )
        if profile is None:
            raise serializers.ValidationError("This user cannot be added to this game.")
        return profile.user

    def validate_user_id(self, value):
        self._resolve_addable_user(value)
        return value

    def create(self, validated_data):
        return self.context["game"].seat(
            self._resolve_addable_user(validated_data["user_id"])
        )

    def to_representation(self, instance):
        return MemberSerializer(instance, context=self.context).data


class MemberNationPreferenceSerializer(serializers.Serializer):
    nation_ids = serializers.ListField(child=serializers.CharField())

    def validate_nation_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate nations in preference list.")
        game = self.context["game"]
        nations = {
            n.nation_id: n for n in game.variant.nations.all() if not n.non_playable
        }
        invalid = [nation_id for nation_id in value if nation_id not in nations]
        if invalid:
            raise serializers.ValidationError(
                f"Invalid nations for this variant: {', '.join(invalid)}."
            )
        self._validated_nations = [nations[nation_id] for nation_id in value]
        return value

    def update(self, instance, validated_data):
        Member.objects.set_nation_preferences(instance, self._validated_nations)
        return instance

    def to_representation(self, instance):
        return {
            "nation_ids": [
                preference.nation.nation_id
                for preference in instance.nation_preferences.select_related("nation")
            ]
        }


class MemberNationAssignSerializer(serializers.Serializer):
    nation_id = serializers.CharField(write_only=True)

    def validate_nation_id(self, value):
        game = self.context["game"]
        nations = {
            n.nation_id: n for n in game.variant.nations.all() if not n.non_playable
        }
        nation = nations.get(value)
        if nation is None:
            raise serializers.ValidationError("Invalid nation for this variant.")
        taken = (
            game.members.not_replaced()
            .filter(nation=nation)
            .exclude(id=self.instance.id)
            .exists()
        )
        if taken:
            raise serializers.ValidationError(
                "This nation is already assigned to another player."
            )
        self._validated_nation = nation
        return value

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                Member.objects.assign_nation(instance, self._validated_nation)
        except IntegrityError:
            raise serializers.ValidationError(
                {"nation_id": "This nation is already assigned to another player."}
            )
        return instance

    def to_representation(self, instance):
        return MemberSerializer(instance, context=self.context).data


class MemberReplaceSerializer(serializers.Serializer):

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user

        with transaction.atomic():
            member = Member.objects.select_for_update().get(
                pk=self.context["replaced_member"].pk
            )
            if not member.replaceable:
                raise serializers.ValidationError(
                    "This seat is not open for replacement."
                )
            nation_name = member.nation.name if member.nation else None
            replacement = Member.objects.hand_over_seat(member, user)
            emit("seat_filled", game=game, actor=user, nation_name=nation_name)

        return replacement

    def to_representation(self, instance):
        return MemberSerializer(instance, context=self.context).data
