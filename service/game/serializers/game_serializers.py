from rest_framework import serializers
import json

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


class NationOptionsSerializer(serializers.Serializer):
    nation = serializers.CharField()
    options = serializers.DictField()

    def to_representation(self, instance):
        return {
            'nation': instance['nation'],
            'options': json.loads(instance['options']) if instance.get('options') else {}
        }


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
    options = NationOptionsSerializer(many=True, source="options_list")


class GameSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    status = serializers.CharField()
    movement_phase_duration = serializers.CharField()
    nation_assignment = serializers.CharField()
    can_join = serializers.BooleanField()
    can_leave = serializers.BooleanField()
    current_phase = PhaseSerializer()
    phases = PhaseSerializer(many=True)
    members = MemberSerializer(many=True)
    variant = VariantSerializer()
    phase_confirmed = serializers.BooleanField()
    can_confirm_phase = serializers.BooleanField()

