from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field


class GameSummarySerializer(serializers.Serializer):
    name = serializers.CharField()
    status = serializers.CharField()


class MemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.CharField(source="user.profile.name", read_only=True)
    picture = serializers.CharField(source="user.profile.picture", read_only=True)
    nation = serializers.CharField(allow_null=True, read_only=True, source="nation.name")
    is_current_user = serializers.SerializerMethodField()
    game = GameSummarySerializer(read_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_is_current_user(self, obj):
        return obj.user == self.context["request"].user

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user
        return game.members.create(user=user)
