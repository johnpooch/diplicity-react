from rest_framework import serializers

from common.serializers import OutputSerializer
from member.serializers import BaseMemberSerializer

from .loaders import RatingPairingLoader, RatingResultLoader
from .models import RatingPairing, RatingResult


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
