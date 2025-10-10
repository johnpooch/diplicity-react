from collections import defaultdict
from rest_framework import serializers

from common.constants import OrderType, UnitType


class AdjudcationOrderSerializer(serializers.Serializer):
    nation = serializers.CharField()
    source = serializers.CharField()
    target = serializers.CharField(allow_null=True)
    aux = serializers.CharField(allow_null=True)
    order_type = serializers.CharField()
    unit_type = serializers.CharField(allow_null=True)


class AdjudicationSerializer(serializers.Serializer):
    Season = serializers.CharField(source="season")
    Year = serializers.IntegerField(source="year")
    Type = serializers.CharField(source="type")
    Options = serializers.JSONField(source="options", read_only=True)
    SupplyCenters = serializers.DictField(source="supply_centers_godip", read_only=True)
    Units = serializers.DictField(source="units_godip")
    Orders = serializers.DictField(source="orders_godip", allow_null=True)
    Resolutions = serializers.DictField(source="resolutions_godip", allow_null=True)
    Dislodgeds = serializers.DictField(source="dislodgeds_godip", allow_null=True)
    Dislodgers = serializers.DictField(source="dislodgers_godip", allow_null=True)
    Bounces = serializers.DictField(source="bounces_godip", default=dict)

    supply_centers = serializers.ListField(allow_null=True, write_only=True)
    resolutions = serializers.ListField(allow_null=True, write_only=True)
    units = serializers.ListField(allow_null=True, write_only=True)
    options = serializers.JSONField(allow_null=True, write_only=True)

    def to_representation(self, instance):
        """
        Convert Phase instance into an object with the expected shape
        """
        # Marshall supply centers into a list of dicts, { province_id: nation_name }
        instance.supply_centers_godip = {
            supply_center.province.province_id: supply_center.nation.name
            for supply_center in instance.supply_centers.all()
        }

        # Marshall units into a dict, { province_id: { Type: unit_type, Nation: unit_nation } }
        temp_dict = defaultdict(dict)
        for unit in instance.units.filter(dislodged_by__isnull=True):
            temp_dict[unit.province.province_id] = {
                "Type": unit.type,
                "Nation": unit.nation.name,
            }
        instance.units_godip = dict(temp_dict)

        # Marshall dislodged units into a dict, { province_id: { Type: unit_type, Nation: unit_nation } }
        temp_dict = defaultdict(dict)
        for unit in instance.units.filter(dislodged_by__isnull=False):
            temp_dict[unit.province.province_id] = {
                "Type": unit.type,
                "Nation": unit.nation.name,
            }
        instance.dislodgeds_godip = dict(temp_dict)

        # Get all of the dislodgers
        temp_dict = defaultdict(dict)
        for unit in instance.units.filter(dislodged_by__isnull=False):
            temp_dict[unit.province.province_id] = unit.dislodged_by.province.province_id
        instance.dislodgers_godip = dict(temp_dict)

        # Marshall orders into a dict: { nation: { source: [...] }}
        temp_dict = defaultdict(dict)
        for order in instance.all_orders:
            if order.order_type == OrderType.BUILD and order.unit_type == UnitType.FLEET and order.named_coast:
                temp_dict[order.nation.name][order.named_coast.province_id] = [order.order_type, order.unit_type]
            elif order.order_type == OrderType.MOVE and order.named_coast:
                temp_dict[order.nation.name][order.source.province_id] = [
                    order.order_type,
                    order.named_coast.province_id,
                ]
            else:
                temp_dict[order.nation.name][order.selected[0]] = order.selected[1:]
        instance.orders_godip = dict(temp_dict)

        instance.resolutions_godip = {}

        return super().to_representation(instance)

    def to_internal_value(self, data):
        """
        Normalize response from API to a dict with the expected shape
        """
        variant = self.context["game"].variant
        phase = data["phase"]

        # Marshall supply centers into a list of dicts
        supply_centers = [
            {"province": province_id, "nation": nation_name}
            for province_id, nation_name in phase["SupplyCenters"].items()
        ]

        # Marshall units into a list of dicts
        units = [
            {
                "province": province_id,
                "type": unit_data["Type"],
                "nation": unit_data["Nation"],
                "dislodged_by": None,
            }
            for province_id, unit_data in phase["Units"].items()
        ]
        dislodgeds = [
            {
                "province": province_id,
                "type": unit_data["Type"],
                "nation": unit_data["Nation"],
                "dislodged_by": (
                    next((k for k, v in phase["Dislodgers"].items() if v == province_id), None)
                    if phase.get("Dislodgers")
                    else None
                ),
            }
            for province_id, unit_data in phase["Dislodgeds"].items()
        ]

        # Merge units and dislodgeds
        units.extend(dislodgeds)

        resolutions = []
        for province, result in phase["Resolutions"].items():
            # Check if the resolution is for a named coast - if it is, set the source to the parent province
            if variant.provinces.filter(province_id=province, parent__isnull=False).exists():
                source = variant.provinces.get(province_id=province).parent.province_id
            else:
                source = province
            resolutions.append(
                {
                    "province": source,
                    "result": result.split(":")[0] if ":" in result else result,
                    "by": result.split(":")[1] if ":" in result else None,
                }
            )

        # Filter options to only include variant nations
        options = {
            nation: options
            for nation, options in data["options"].items()
            if nation in variant.nations.all().values_list("name", flat=True)
        }

        merged_data = {
            **phase,
            "options": options,
            "supply_centers": supply_centers,
            "units": units,
            "resolutions": resolutions,
        }
        internal_value = super().to_internal_value(merged_data)
        return internal_value
