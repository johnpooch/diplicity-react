from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field


class GameSummarySerializer(serializers.Serializer):
    name = serializers.CharField()
    status = serializers.CharField()


class MemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source="user.profile.name", read_only=True)
    picture = serializers.CharField(source="user.profile.picture", read_only=True)
    nation = serializers.CharField(allow_null=True, read_only=True, source="nation.name")
    is_current_user = serializers.SerializerMethodField()
    game = GameSummarySerializer(read_only=True)
    supply_center_count = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField)
    def get_is_current_user(self, obj):
        return obj.user == self.context["request"].user

    @extend_schema_field(serializers.IntegerField)
    def get_supply_center_count(self, obj):
        current_phase = obj.game.current_phase
        if not current_phase:
            return 0
        return sum(1 for sc in current_phase.supply_centers.all() if sc.nation_id == obj.nation_id)

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user
        return game.members.create(user=user)
