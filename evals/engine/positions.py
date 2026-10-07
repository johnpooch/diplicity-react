from engine.rules import legal_options, resolve

MOVE = "Move"
MOVE_VIA_CONVOY = "MoveViaConvoy"
RETREAT = "Retreat"
BUILD = "Build"
HOLD = "Hold"
DISBAND = "Disband"
SUPPORT = "Support"
CONVOY = "Convoy"
FLEET = "Fleet"
ARMY = "Army"


class Board:
    def __init__(self, variant: dict):
        self.variant = variant
        self.nation_ids = {nation["name"]: nation["id"] for nation in variant["nations"]}
        self.nation_names = {nation["id"]: nation["name"] for nation in variant["nations"]}
        self.parents = {coast["id"]: coast["parentProvince"] for coast in variant.get("namedCoasts", [])}

    def parent(self, location: str) -> str:
        return self.parents.get(location, location)

    def coasts(self, province: str) -> set[str]:
        return {coast for coast, parent in self.parents.items() if parent == province}

    def game_state(self, phase, units, supply_centers, contested_provinces=(), orders=None) -> dict:
        return {
            "phase": {"season": phase["season"], "year": phase["year"], "type": phase["type"]},
            "units": [
                {
                    "nation": self.nation_ids[unit["nation"]],
                    "type": unit["type"],
                    "location": unit["province"],
                    "dislodged": unit.get("dislodged", False),
                    "dislodgedFrom": unit.get("dislodged_from"),
                }
                for unit in units
            ],
            "supplyCenters": [
                {"nation": self.nation_ids[center["nation"]], "province": center["province"]}
                for center in supply_centers
            ],
            "orders": self.raw_orders(phase["type"], orders or {}),
            "contestedProvinces": list(contested_provinces),
        }

    def options_by_nation(self, state: dict) -> dict[str, list[dict]]:
        retreat = state["phase"]["type"] == RETREAT
        nation_at = {unit["location"]: unit["nation"] for unit in state["units"] if unit["dislodged"] == retreat}
        owners = {center["province"]: center["nation"] for center in state["supplyCenters"]}
        by_nation: dict[str, list[dict]] = {}
        builds: dict[tuple[str, str], dict[str, set[str]]] = {}
        for option in legal_options(self.variant, state):
            source = option["source"]
            if option["orderType"] == BUILD:
                owner = owners.get(self.parent(source))
                if owner is not None:
                    by_type = builds.setdefault((owner, self.parent(source)), {})
                    by_type.setdefault(option["unitType"] or ARMY, set()).add(source)
                continue
            nation = nation_at.get(source) if retreat else nation_at.get(source, owners.get(self.parent(source)))
            if nation is None:
                continue
            by_nation.setdefault(self.nation_names[nation], []).append(self._option(option, retreat))
        for (owner, province), by_type in builds.items():
            by_nation.setdefault(self.nation_names[owner], []).extend(self._builds(province, by_type))
        return by_nation

    def _option(self, option, retreat):
        order_type = MOVE if retreat and option["orderType"] == RETREAT else option["orderType"]
        result = {"source": self.parent(option["source"]), "order_type": order_type}
        if order_type in (MOVE, MOVE_VIA_CONVOY):
            result["target"] = self.parent(option["target"])
            if option["target"] != result["target"]:
                result["named_coast"] = option["target"]
        elif order_type in (SUPPORT, CONVOY):
            result["target"] = option["target"]
            result["aux"] = option["aux"]
        return result

    def _builds(self, province, by_type):
        fleet_coasts = sorted(by_type.get(FLEET, set()) & self.coasts(province))
        if len(fleet_coasts) == 1:
            coast = fleet_coasts[0]
            unit_types = [unit_type for unit_type in (ARMY, FLEET) if unit_type in by_type]
            return [{"source": coast, "order_type": BUILD, "unit_type": unit_type} for unit_type in unit_types]
        if fleet_coasts:
            army = [{"source": province, "order_type": BUILD, "unit_type": ARMY}] if ARMY in by_type else []
            fleets = [
                {"source": province, "order_type": BUILD, "unit_type": FLEET, "named_coast": coast}
                for coast in fleet_coasts
            ]
            return army + fleets
        return [{"source": province, "order_type": BUILD, "unit_type": unit_type} for unit_type in sorted(by_type)]

    def raw_orders(self, phase_type, orders_by_nation) -> list[dict]:
        return [
            self._raw_order(nation, option, phase_type)
            for nation, options in sorted(orders_by_nation.items())
            for option in options
        ]

    def _raw_order(self, nation, option, phase_type):
        order_type = option["order_type"]
        via_convoy = False
        if phase_type == RETREAT and order_type == MOVE:
            order_type = RETREAT
        elif order_type == MOVE_VIA_CONVOY:
            order_type = MOVE
            via_convoy = True
        source = option["source"]
        target = option.get("target")
        named_coast = option.get("named_coast")
        if named_coast is not None:
            if order_type == BUILD:
                source = named_coast
            else:
                target = named_coast
        return {
            "nation": self.nation_ids[nation],
            "source": source,
            "orderType": order_type,
            "target": target,
            "aux": option.get("aux"),
            "unitType": option.get("unit_type"),
            "viaConvoy": via_convoy,
        }

    def outcome(self, state: dict, orders_by_nation: dict[str, list[dict]]) -> tuple[dict, dict]:
        orders = self.raw_orders(state["phase"]["type"], orders_by_nation)
        resolved, following = resolve(self.variant, {**state, "orders": orders})
        results = {self.parent(resolution["province"]): resolution["code"] for resolution in resolved["resolutions"]}
        resolutions = [
            {"nation": nation, "source": option["source"], "result": results[self.parent(option["source"])]}
            for nation, options in sorted(orders_by_nation.items())
            for option in options
            if self.parent(option["source"]) in results
        ]
        outcome = {
            "resolutions": resolutions,
            "units": self.fixture_units(following["units"]),
            "supply_centers": self.fixture_supply_centers(following["supplyCenters"]),
        }
        return outcome, following

    def fixture_units(self, units) -> list[dict]:
        return sorted(
            (
                {
                    "type": unit["type"],
                    "nation": self.nation_names[unit["nation"]],
                    "province": unit["location"],
                    **({"dislodged": True} if unit["dislodged"] else {}),
                    **({"dislodged_from": unit["dislodgedFrom"]} if unit.get("dislodgedFrom") else {}),
                }
                for unit in units
            ),
            key=lambda unit: (unit["province"], unit.get("dislodged", False)),
        )

    def fixture_supply_centers(self, supply_centers) -> list[dict]:
        return sorted(
            (
                {"nation": self.nation_names[center["nation"]], "province": center["province"]}
                for center in supply_centers
            ),
            key=lambda center: center["province"],
        )
