import re

from rest_framework import serializers

from user_profile.models import default_colour_profile as _default_colour_profile

_HEX_COLOUR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_COLOUR_PROFILE_LENGTH = 30


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(min_length=2, max_length=255)
    picture = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.CharField(source="user.email", read_only=True)
    colour_profile_enabled = serializers.BooleanField()
    custom_colour_profile = serializers.ListField(child=serializers.CharField(max_length=7))
    default_colour_profile = serializers.SerializerMethodField()

    def get_default_colour_profile(self, obj):
        return _default_colour_profile()

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        if not all(c.isalpha() or c.isspace() or c in "-'" for c in value):
            raise serializers.ValidationError("Name can only contain letters, spaces, hyphens, and apostrophes.")
        return value

    def validate_custom_colour_profile(self, value):
        if len(value) != _COLOUR_PROFILE_LENGTH:
            raise serializers.ValidationError(
                f"custom_colour_profile must contain exactly {_COLOUR_PROFILE_LENGTH} items."
            )
        for colour in value:
            if not _HEX_COLOUR_RE.match(colour):
                raise serializers.ValidationError(
                    f"'{colour}' is not a valid hex colour. Each item must match #RRGGBB."
                )
        return value

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.colour_profile_enabled = validated_data.get(
            "colour_profile_enabled", instance.colour_profile_enabled
        )
        instance.custom_colour_profile = validated_data.get(
            "custom_colour_profile", instance.custom_colour_profile
        )
        instance.save()
        return instance
