from rest_framework import serializers
from province.serializers import ProvinceSerializer
from nation.serializers import NationSerializer
from phase.serializers import PhaseRetrieveSerializer


class VariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = NationSerializer(many=True)
    provinces = ProvinceSerializer(many=True)
    template_phase = PhaseRetrieveSerializer()


class GameListVariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = NationSerializer(many=True)
