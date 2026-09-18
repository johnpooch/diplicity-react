from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from common.constants import PlayerGameOutcome
from nation.serializers import NationSerializer
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
    reliability_tier = serializers.CharField(read_only=True, allow_null=True)
    commitment = serializers.CharField(read_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_can_create_bot_games(self, obj):
        return user_can_use_bot_opponent(obj.user)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        stats = get_player_stats(instance.user)
        data["reliability_tier"] = stats.get("reliability_tier")
        return data

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        if not all(c.isalpha() or c.isspace() or c in "-'" for c in value):
            raise serializers.ValidationError("Name can only contain letters, spaces, hyphens, and apostrophes.")
        return value

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance


class AddableUserSerializer(PictureUrlMixin, serializers.Serializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(read_only=True)
    picture = serializers.SerializerMethodField()


class FavouriteNationSerializer(serializers.Serializer):
    nation = NationSerializer(read_only=True)
    games_played = serializers.IntegerField(read_only=True)


class PlayerGameResultSerializer(serializers.Serializer):
    game_id = serializers.CharField(read_only=True)
    game_name = serializers.CharField(read_only=True)
    nation = NationSerializer(read_only=True)
    outcome = serializers.ChoiceField(choices=PlayerGameOutcome.OUTCOME_CHOICES, read_only=True)
    finished_at = serializers.DateTimeField(read_only=True)


class PublicUserProfileSerializer(PictureUrlMixin, serializers.Serializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(read_only=True)
    picture = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    total_games = serializers.IntegerField(read_only=True)
    solo_wins = serializers.IntegerField(read_only=True)
    draws = serializers.IntegerField(read_only=True)
    losses = serializers.IntegerField(read_only=True)
    nmr_rate = serializers.FloatField(read_only=True)
    cd_rate = serializers.FloatField(read_only=True)
    reliability_tier = serializers.CharField(read_only=True, allow_null=True)
    commitment = serializers.CharField(read_only=True)
    favourite_nation = FavouriteNationSerializer(read_only=True, allow_null=True)
    recent_results = PlayerGameResultSerializer(read_only=True, many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        stats = get_player_stats(instance.user)
        favourite_nation = stats.pop("favourite_nation")
        recent_results = stats.pop("recent_results")
        data.update(stats)
        data["favourite_nation"] = (
            FavouriteNationSerializer(favourite_nation, context=self.context).data
            if favourite_nation
            else None
        )
        data["recent_results"] = PlayerGameResultSerializer(
            recent_results, many=True, context=self.context
        ).data
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
