from rest_framework import serializers


class ProvinceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()


class NationSerializer(serializers.Serializer):
    name = serializers.CharField()
    color = serializers.CharField()


class StartSerializer(serializers.Serializer):
    season = serializers.CharField()
    year = serializers.CharField()
    type = serializers.CharField()
    units = serializers.ListField(child=serializers.DictField())
    supply_centers = serializers.ListField(child=serializers.DictField())


class VariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = NationSerializer(many=True)
    start = StartSerializer()
    provinces = ProvinceSerializer(many=True)
