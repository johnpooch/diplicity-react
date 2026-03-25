from rest_framework import serializers
import re

from member.models import Member
from common.constants import GameStatus


class UserAccountDeleteSerializer(serializers.Serializer):
    confirm = serializers.CharField(write_only=True)

    def validate_confirm(self, value):
        if value != "DELETE":
            raise serializers.ValidationError("You must type DELETE to confirm account deletion.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        user_members = Member.objects.filter(user=user)
        user_members.filter(game__status=GameStatus.PENDING).delete()
        user_members.filter(
            game__status__in=[GameStatus.ACTIVE, GameStatus.COMPLETED]
        ).update(kicked=True)
        user.delete()
        return validated_data


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(min_length=2, max_length=255)
    picture = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.CharField(source="user.email", read_only=True)

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
