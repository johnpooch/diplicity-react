from rest_framework import serializers

from bot.constants import BotKind
from common.constants import (
    CommitmentBand,
    CommitmentEvent,
    CommitmentShade,
)
from common.serializers import AbsoluteUrlField, derived, hydrated
from report.constants import ReportReason

from .loaders import PublicUserProfileLoader, UserProfileLoader
from .models import UserProfilePicture
from .utils import normalise_picture


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(min_length=2, max_length=255)
    picture = AbsoluteUrlField(source="picture_path")
    email = serializers.CharField(source="user.email", read_only=True)
    can_create_bot_games = serializers.BooleanField(read_only=True)
    is_moderator = serializers.BooleanField(read_only=True)
    can_create_committed_game = hydrated(serializers.BooleanField(read_only=True))

    class Meta:
        loader = UserProfileLoader

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError(
                "Name must be at least 2 characters long."
            )
        if not all(c.isalpha() or c.isspace() or c in "-'" for c in value):
            raise serializers.ValidationError(
                "Name can only contain letters, spaces, hyphens, and apostrophes."
            )
        return value

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return UserProfileLoader.get(instance.pk, self.context["request"].user)


class AddableUserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(read_only=True)
    picture = AbsoluteUrlField(source="picture_path")


class CommitmentBreakdownSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(
        choices=CommitmentEvent.KIND_CHOICES, read_only=True
    )
    count = serializers.IntegerField(read_only=True)
    points = serializers.IntegerField(read_only=True)


class CommitmentSquareSerializer(serializers.Serializer):
    anonymous = serializers.BooleanField(
        source="game.anonymity_active", read_only=True
    )
    game_name = derived(
        serializers.CharField(source="public_game_name", read_only=True, allow_null=True)
    )
    submitted = serializers.IntegerField(read_only=True, source="commitment_submitted")
    missed = serializers.IntegerField(read_only=True, source="commitment_missed")
    breakdown = CommitmentBreakdownSerializer(
        many=True, read_only=True, source="commitment_breakdown"
    )
    points = serializers.IntegerField(read_only=True, source="commitment_square")
    shade = derived(
        serializers.ChoiceField(
            source="commitment_shade",
            choices=CommitmentShade.SHADE_CHOICES,
            read_only=True,
        )
    )


class MarkSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(
        choices=ReportReason.REASON_CHOICES, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)


class ProfileRatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(source="rounded_rating", read_only=True)
    rank = serializers.IntegerField(read_only=True, allow_null=True)
    won = serializers.IntegerField(read_only=True)
    drew = serializers.IntegerField(read_only=True)
    lost = serializers.IntegerField(read_only=True)


class PublicUserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(read_only=True)
    picture = AbsoluteUrlField(source="picture_path")
    bot_kind = derived(
        serializers.ChoiceField(
            source="user.bot.kind",
            choices=BotKind.KIND_CHOICES,
            read_only=True,
            allow_null=True,
        )
    )
    created_at = derived(
        serializers.DateTimeField(
            source="public_created_at", read_only=True, allow_null=True
        )
    )
    total_games = hydrated(serializers.IntegerField(read_only=True))
    active_games = hydrated(serializers.IntegerField(read_only=True))
    commitment_total = serializers.IntegerField(read_only=True)
    commitment_band = derived(
        serializers.ChoiceField(choices=CommitmentBand.BAND_CHOICES, read_only=True)
    )
    commitment_squares = hydrated(CommitmentSquareSerializer(many=True, read_only=True))
    rating = hydrated(ProfileRatingSerializer(read_only=True, allow_null=True))
    marks = hydrated(MarkSerializer(many=True, read_only=True))

    class Meta:
        loader = PublicUserProfileLoader


class UserProfilePictureSerializer(serializers.Serializer):
    picture = serializers.FileField(write_only=True)

    def validate_picture(self, value):
        return normalise_picture(value)

    def update(self, instance, validated_data):
        data, content_type = validated_data["picture"]
        UserProfilePicture.objects.store(instance, data, content_type)
        return UserProfileLoader.get(instance.pk, self.context["request"].user)

    def to_representation(self, instance):
        return UserProfileSerializer(instance, context=self.context).data
