from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from bot_profile.utils import user_can_use_bot_opponent
from .utils import get_player_stats


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(min_length=2, max_length=255)
    picture = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.CharField(source="user.email", read_only=True)
    email_notifications_enabled = serializers.BooleanField(required=False)
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
        instance.email_notifications_enabled = validated_data.get(
            "email_notifications_enabled", instance.email_notifications_enabled
        )
        instance.save()
        return instance


class PublicUserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(read_only=True)
    picture = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    total_games = serializers.IntegerField(read_only=True)
    solo_wins = serializers.IntegerField(read_only=True)
    draws = serializers.IntegerField(read_only=True)
    losses = serializers.IntegerField(read_only=True)
    nmr_rate = serializers.FloatField(read_only=True)
    cd_rate = serializers.FloatField(read_only=True)
    reliability_tier = serializers.CharField(read_only=True, allow_null=True)
    commitment = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        stats = get_player_stats(instance.user)
        data.update(stats)
        return data
