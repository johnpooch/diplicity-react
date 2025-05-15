from rest_framework import serializers


class AdjudicationGameSerializer(serializers.Serializer):
    Year = serializers.IntegerField(source="current_phase.year")
    Season = serializers.CharField(source="current_phase.season")
    Type = serializers.CharField(source="current_phase.type")
    Units = serializers.SerializerMethodField()
    SupplyCenters = serializers.SerializerMethodField()
    Dislodgeds = serializers.SerializerMethodField()
    Dislodgers = serializers.SerializerMethodField()
    Bounces = serializers.SerializerMethodField()
    Resolutions = serializers.SerializerMethodField()
    Orders = serializers.SerializerMethodField()

    def get_Bounces(self, obj):
        return {}

    def get_Dislodgers(self, obj):
        return {
            unit.dislodged_by: unit.province
            for unit in obj.current_phase.units.filter(dislodged_by__isnull=False)
        }

    def get_Dislodgeds(self, obj):
        return {
            unit.province: {
                "Type": unit.type,
                "Nation": unit.nation,
            }
            for unit in obj.current_phase.units.filter(dislodged=True)
        }

    def get_Resolutions(self, obj):
        return {}

    def get_Units(self, obj):
        return {
            unit.province: {
                "Type": unit.type,
                "Nation": unit.nation,
            }
            for unit in obj.current_phase.units.filter(dislodged=False)
        }

    def get_SupplyCenters(self, obj):
        return {
            supply_center.province: supply_center.nation
            for supply_center in obj.current_phase.supply_centers.all()
        }

    def get_Orders(self, obj):
        orders = {}
        for phase_state in obj.current_phase.phase_states.all():
            nation_orders = {}
            for order in phase_state.orders.all():
                parts = [
                    order.order_type,
                ]
                if order.target:
                    parts.append(order.target)
                if order.aux:
                    parts.append(order.aux)
                nation_orders[order.source] = parts
            orders[phase_state.member.nation] = nation_orders

        return orders


class AdjudicationResponseUnitSerializer(serializers.Serializer):
    Type = serializers.CharField(source="type")
    Nation = serializers.CharField(source="nation")
    Province = serializers.CharField(source="province")
    Dislodged = serializers.BooleanField(source="dislodged", required=False)
    DislodgedBy = serializers.CharField(
        source="dislodged_by", required=False, allow_null=True
    )


class AdjudicationResponseSupplyCenterSerializer(serializers.Serializer):
    Province = serializers.CharField(source="province")
    Nation = serializers.CharField(source="nation")


class AdjudicationResponseResolutionSerializer(serializers.Serializer):
    Province = serializers.CharField(source="province")
    Result = serializers.ChoiceField(
        source="result",
        choices=[
            "OK",
            "ErrIllegalMove",
            "ErrIllegalDestination",
            "ErrBounce",
            "ErrInvalidSupporteeOrder",
            "ErrIllegalSupportDestination",
            "ErrInvalidDestination",
        ],
    )
    By = serializers.CharField(source="by", required=False, allow_null=True)


class AdjudicationResponsePhaseSerializer(serializers.Serializer):
    Season = serializers.CharField(source="season")
    Year = serializers.IntegerField(source="year")
    Type = serializers.CharField(source="type")
    Units = AdjudicationResponseUnitSerializer(many=True, source="units")
    SupplyCenters = AdjudicationResponseSupplyCenterSerializer(
        many=True, source="supply_centers"
    )
    Resolutions = AdjudicationResponseResolutionSerializer(
        many=True, source="resolutions"
    )

    def to_internal_value(self, data):
        dislodgeds = data.get("Dislodgeds", {})
        dislodgers = {value: key for key, value in data.get("Dislodgers", {}).items()}

        data["Units"] = [
            {
                "Province": key,
                **value,
            }
            for key, value in data["Units"].items()
        ]

        for province, unit in dislodgeds.items():
            data["Units"].append(
                {
                    "Province": province,
                    "Type": unit["Type"],
                    "Nation": unit["Nation"],
                    "Dislodged": True,
                    "DislodgedBy": dislodgers.get(province),
                }
            )

        data["SupplyCenters"] = [
            {"Province": province, "Nation": nation}
            for province, nation in data["SupplyCenters"].items()
        ]
        data["Bounces"] = [
            {"Province": key, **value} for key, value in data["Bounces"].items()
        ]
        data["Resolutions"] = [
            {
                "Province": key,
                "Result": result.split(":")[0] if ":" in result else result,
                "By": result.split(":")[1] if ":" in result else None,
            }
            for key, result in data["Resolutions"].items()
        ]
        return super().to_internal_value(data)


class AdjudicationResponseSerializer(serializers.Serializer):
    phase = AdjudicationResponsePhaseSerializer()
    options = serializers.DictField()
