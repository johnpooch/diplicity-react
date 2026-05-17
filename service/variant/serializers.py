from typing import Optional

from django.urls import reverse
from rest_framework import serializers
from province.serializers import ProvinceSerializer
from nation.serializers import NationSerializer
from phase.serializers import PhaseRetrieveSerializer

from .models import VariantSvg


class VictoryConditionsSerializer(serializers.Serializer):
    solo_victory_supply_centers = serializers.IntegerField(source="soloVictorySupplyCenters")
    game_ends_year = serializers.IntegerField(source="gameEndsYear", allow_null=True)
    draw_after_year = serializers.IntegerField(source="drawAfterYear", allow_null=True)


class VariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    rules = serializers.CharField(allow_blank=True)
    victory_conditions = VictoryConditionsSerializer()
    svg_url = serializers.SerializerMethodField()
    nations = NationSerializer(many=True)
    provinces = ProvinceSerializer(many=True)
    template_phase = PhaseRetrieveSerializer()

    def get_svg_url(self, variant) -> Optional[str]:
        try:
            variant_svg = variant.svg
        except VariantSvg.DoesNotExist:
            return None
        path = reverse(
            "variant-svg",
            kwargs={"variant_id": variant.id, "content_hash": variant_svg.content_hash},
        )
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path


class GameListVariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = NationSerializer(many=True)
