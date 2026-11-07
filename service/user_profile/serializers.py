from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from common.constants import (
    CommitmentBand,
    CommitmentEvent,
    CommitmentRequirement,
    CommitmentShade,
)
from game.models import Game
from member.checks import MeetsCommitmentRequirementCheck
from member.models import Member
from rating.models import Rating
from report.constants import ReportReason
from report.models import Mark

from .models import UserProfile, UserProfilePicture
from .utils import get_player_stats, normalise_picture, user_can_use_bot_opponent


class PictureUrlMixin:
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_picture(self, obj):
        return obj.picture_url(self.context.get("request"))


class UserProfileSerializer(PictureUrlMixin, serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(min_length=2, max_length=255)
    picture = serializers.SerializerMethodField()
    email = serializers.CharField(source="user.email", read_only=True)
    can_create_bot_games = serializers.SerializerMethodField()
    is_moderator = serializers.BooleanField(read_only=True)
    can_create_committed_game = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField)
    def get_can_create_bot_games(self, obj):
        return user_can_use_bot_opponent(obj.user)

    @extend_schema_field(serializers.BooleanField)
    def get_can_create_committed_game(self, obj):
        return MeetsCommitmentRequirementCheck.decide(
            Game(commitment_requirement=CommitmentRequirement.COMMITTED), obj.user
        ).allowed

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
        UserProfile.objects.save_profile(instance)
        return instance


class AddableUserSerializer(PictureUrlMixin, serializers.Serializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(read_only=True)
    picture = serializers.SerializerMethodField()


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
    game_name = serializers.SerializerMethodField()
    submitted = serializers.IntegerField(read_only=True, source="commitment_submitted")
    missed = serializers.IntegerField(read_only=True, source="commitment_missed")
    breakdown = CommitmentBreakdownSerializer(
        many=True, read_only=True, source="commitment_breakdown"
    )
    points = serializers.IntegerField(read_only=True, source="commitment_square")
    shade = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_game_name(self, obj):
        if obj.game.anonymity_active:
            return None
        return obj.game.name

    @extend_schema_field(serializers.ChoiceField(choices=CommitmentShade.SHADE_CHOICES))
    def get_shade(self, obj):
        return CommitmentShade.for_points(obj.commitment_square)


class MarkSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(
        choices=ReportReason.REASON_CHOICES, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)


class ProfileRatingSerializer(serializers.Serializer):
    rating = serializers.SerializerMethodField()
    rank = serializers.IntegerField(read_only=True, allow_null=True)
    won = serializers.IntegerField(read_only=True)
    drew = serializers.IntegerField(read_only=True)
    lost = serializers.IntegerField(read_only=True)

    @extend_schema_field(serializers.IntegerField)
    def get_rating(self, obj):
        return round(obj.rating)


class PublicUserProfileSerializer(PictureUrlMixin, serializers.Serializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(read_only=True)
    picture = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    total_games = serializers.IntegerField(read_only=True)
    active_games = serializers.IntegerField(read_only=True)
    commitment_total = serializers.IntegerField(read_only=True)
    commitment_band = serializers.SerializerMethodField()
    commitment_squares = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    marks = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ChoiceField(choices=CommitmentBand.BAND_CHOICES))
    def get_commitment_band(self, obj):
        return CommitmentBand.for_total(obj.commitment_total)

    @extend_schema_field(CommitmentSquareSerializer(many=True))
    def get_commitment_squares(self, obj):
        squares = list(Member.objects.filter(user=obj.user).commitment_squares())
        Member.objects.hydrate_commitment_breakdowns(squares)
        return CommitmentSquareSerializer(squares, many=True).data

    @extend_schema_field(ProfileRatingSerializer(allow_null=True))
    def get_rating(self, obj):
        rating = (
            Rating.objects.filter(user=obj.user)
            .with_rank(timezone.now())
            .with_record()
            .first()
        )
        if rating is None:
            return None
        return ProfileRatingSerializer(rating).data

    @extend_schema_field(MarkSerializer(many=True))
    def get_marks(self, obj):
        marks = Mark.objects.filter(member__user=obj.user).order_by("-created_at")
        return MarkSerializer(marks, many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        stats = get_player_stats(instance.user)
        data.update(stats)
        return data


class UserProfilePictureSerializer(serializers.Serializer):
    picture = serializers.FileField(write_only=True)

    def validate_picture(self, value):
        return normalise_picture(value)

    def update(self, instance, validated_data):
        data, content_type = validated_data["picture"]
        UserProfilePicture.objects.store(instance, data, content_type)
        return instance

    def to_representation(self, instance):
        return UserProfileSerializer(instance, context=self.context).data
