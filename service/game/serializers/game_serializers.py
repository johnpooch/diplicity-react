from rest_framework import serializers

from .variant_serializers import VariantSerializer, NationSerializer


class MemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(source="user.username")
    name = serializers.CharField(source="user.profile.name")
    picture = serializers.CharField(source="user.profile.picture")
    nation = serializers.CharField()
    is_current_user = serializers.BooleanField()


class ProvinceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()


class UnitSerializer(serializers.Serializer):
    type = serializers.CharField()
    nation = NationSerializer(source="nation_data")
    province = ProvinceSerializer(source="province_data")


class SupplyCenterSerializer(serializers.Serializer):
    province = ProvinceSerializer(source="province_data")
    nation = NationSerializer(source="nation_data")


class PhaseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ordinal = serializers.IntegerField()
    season = serializers.CharField()
    year = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    remaining_time = serializers.CharField()
    units = UnitSerializer(many=True)
    supply_centers = SupplyCenterSerializer(many=True)


class GameSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()
    movement_phase_duration = serializers.CharField()
    can_join = serializers.BooleanField()
    can_leave = serializers.BooleanField()
    current_phase = PhaseSerializer()
    members = MemberSerializer(many=True)
    variant = VariantSerializer()
