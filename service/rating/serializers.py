from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from common.serializers import OutputSerializer
from member.serializers import BaseMemberSerializer

from .loaders import LeaderboardEntryLoader, RatingPairingLoader, RatingResultLoader
from .models import Rating, RatingPairing, RatingResult


@extend_schema_serializer(component_name="LeaderboardEntry")
class LeaderboardEntryOutputSerializer(OutputSerializer):
    rank = serializers.IntegerField()
    name = serializers.CharField(source="user.profile.name")
    picture = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        loader = LeaderboardEntryLoader
        fields = ("rank", "user_id", "name", "picture", "rating")

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_picture(self, obj):
        return obj.user.profile.picture_url(self.context.get("request"))


class RatingOpponentSerializer(BaseMemberSerializer):
    nation = serializers.CharField(source="nation.name", allow_null=True)


class RatingPairingOutputSerializer(OutputSerializer):
    opponent = RatingOpponentSerializer()

    class Meta:
        model = RatingPairing
        loader = RatingPairingLoader
        fields = ("id", "opponent", "opponent_rating", "score", "change")


class RatingResultOutputSerializer(OutputSerializer):
    rating_change = serializers.FloatField()
    pairings = RatingPairingOutputSerializer(many=True)

    class Meta:
        model = RatingResult
        loader = RatingResultLoader
        fields = (
            "id",
            "rating_before",
            "rating_after",
            "rating_change",
            "protected",
            "pairings",
        )
