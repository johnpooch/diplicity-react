from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from common.constants import GameStatus


class BaseMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    is_current_user = serializers.SerializerMethodField()

    def _is_current_user(self, obj):
        if obj.user is None:
            return False
        return obj.user == self.context["request"].user

    def _is_masked(self, obj):
        game = self._get_game(obj)
        if not game.anonymous:
            return False
        if game.status == GameStatus.COMPLETED:
            return False
        return not self._is_current_user(obj)

    def _get_game(self, obj):
        if "game" in self.context:
            return self.context["game"]
        return obj.game

    @extend_schema_field(serializers.CharField)
    def get_name(self, obj):
        if self._is_masked(obj):
            return "Anonymous"
        if obj.user is None:
            return "Deleted User"
        return obj.user.profile.name

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_picture(self, obj):
        if self._is_masked(obj):
            return None
        if obj.user is None:
            return None
        return obj.user.profile.picture

    @extend_schema_field(serializers.BooleanField)
    def get_is_current_user(self, obj):
        return self._is_current_user(obj)


class MemberSerializer(BaseMemberSerializer):
    nation = serializers.CharField(allow_null=True, read_only=True, source="nation.name")
    eliminated = serializers.BooleanField(read_only=True)
    kicked = serializers.BooleanField(read_only=True)
    is_game_master = serializers.SerializerMethodField()
    nmr_extensions_remaining = serializers.IntegerField(read_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_is_game_master(self, obj):
        if self._is_masked(obj):
            return False
        return obj.is_game_master

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user
        return game.members.create(user=user)
