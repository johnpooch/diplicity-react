from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from common.constants import CommitmentBand, CommitmentEvent, CommitmentShade
from member.models import Member

from .models import UserProfilePicture
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
    commitment = serializers.CharField(read_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_can_create_bot_games(self, obj):
        return user_can_use_bot_opponent(obj.user)

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


class PublicUserProfileSerializer(PictureUrlMixin, serializers.Serializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(read_only=True)
    picture = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    total_games = serializers.IntegerField(read_only=True)
    active_games = serializers.IntegerField(read_only=True)
    commitment = serializers.CharField(read_only=True)
    commitment_total = serializers.IntegerField(read_only=True)
    commitment_band = serializers.SerializerMethodField()
    commitment_squares = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ChoiceField(choices=CommitmentBand.BAND_CHOICES))
    def get_commitment_band(self, obj):
        return CommitmentBand.for_total(obj.commitment_total)

    @extend_schema_field(CommitmentSquareSerializer(many=True))
    def get_commitment_squares(self, obj):
        squares = list(Member.objects.filter(user=obj.user).commitment_squares())
        Member.objects.hydrate_commitment_breakdowns(squares)
        return CommitmentSquareSerializer(squares, many=True).data

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
