from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field


class MemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source="user.profile.name", read_only=True)
    picture = serializers.CharField(source="user.profile.picture", read_only=True, allow_null=True)
    nation = serializers.CharField(allow_null=True, read_only=True, source="nation.name")
    is_current_user = serializers.SerializerMethodField()
    eliminated = serializers.BooleanField(read_only=True)
    kicked = serializers.BooleanField(read_only=True)
    is_game_master = serializers.BooleanField(read_only=True)
    nmr_extensions_remaining = serializers.IntegerField(read_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_is_current_user(self, obj):
        return obj.user == self.context["request"].user

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user
        return game.members.create(user=user)
