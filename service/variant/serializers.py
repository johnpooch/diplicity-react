from rest_framework import serializers
from province.serializers import ProvinceSerializer
from nation.serializers import NationSerializer


class UnitSerializer(serializers.Serializer):
    type = serializers.CharField()
    nation = NationSerializer()
    province = ProvinceSerializer()
    dislodged = serializers.BooleanField(default=False)


class SupplyCenterSerializer(serializers.Serializer):
    province = ProvinceSerializer()
    nation = NationSerializer()


class TemplatePhaseSerializer(serializers.Serializer):
    season = serializers.CharField()
    year = serializers.IntegerField()
    type = serializers.CharField()
    units = UnitSerializer(many=True)
    supply_centers = SupplyCenterSerializer(many=True)

    def to_representation(self, instance):
        # Get the template phase units and supply centers with proper nation data
        variant = instance.variant

        units = []
        for unit in instance.units.all():
            nation_data = variant.get_nation(unit.nation)
            units.append({
                "type": unit.type,
                "nation": {
                    "name": unit.nation,
                    "color": nation_data.get("color", "#000000") if nation_data else "#000000",
                },
                "province": variant.get_province(unit.province),
                "dislodged": unit.dislodged
            })

        supply_centers = []
        for sc in instance.supply_centers.all():
            nation_data = variant.get_nation(sc.nation)
            supply_centers.append({
                "province": variant.get_province(sc.province),
                "nation": {
                    "name": sc.nation,
                    "color": nation_data.get("color", "#000000") if nation_data else "#000000",
                }
            })

        return {
            "season": instance.season,
            "year": instance.year,
            "type": instance.type,
            "units": units,
            "supply_centers": supply_centers
        }


class VariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = NationSerializer(many=True)
    provinces = ProvinceSerializer(many=True)
    template_phase = TemplatePhaseSerializer()
