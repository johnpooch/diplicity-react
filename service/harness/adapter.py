import json
from pathlib import Path

from harness.exceptions import ContextError, FixtureError
from harness.generated.api import (
    FieldValue,
    FlatOrderOption,
    Member as ApiMember,
    Nation as ApiNation,
    PhaseState as ApiPhaseState,
    Province as ApiProvince,
    SupplyCenter as ApiSupplyCenter,
    Unit as ApiUnit,
    VariantProvince as ApiVariantProvince,
)
from harness.types import (
    Adjacency,
    ApiData,
    ApiVariant,
    Channel,
    Context,
    Member,
    OrderOption,
    Province,
    SelectOrdersFixture,
    SupplyCenter,
    Unit,
)

VARIANTS_DIR = Path(__file__).parent / "data" / "variants"

PASS_TO_ALLOWS = {
    "army": ["army"],
    "fleet": ["fleet"],
    "both": ["army", "fleet"],
}


def load_variant(variant_id: str) -> ApiVariant:
    path = VARIANTS_DIR / f"{variant_id}.json"
    if not path.exists():
        raise FixtureError(f"unknown variant '{variant_id}'")
    return json.loads(path.read_text())


def _field(value: str | None, label: str | None = None) -> FieldValue | None:
    if value is None:
        return None
    return {"id": value, "label": label if label is not None else value}


def _nation(name: str) -> ApiNation:
    return {
        "nation_id": name.lower(),
        "name": name,
        "color": "#000000",
        "non_playable": False,
        "flag_url": None,
    }


def _province(province: ApiVariantProvince) -> ApiProvince:
    return {
        "id": province["id"],
        "name": province["name"],
        "type": province["type"],
        "supply_center": province["supply_center"],
        "parent_id": province["parent_id"],
        "named_coast_ids": [],
    }


def _member(index: int, nation: str, is_current_user: bool) -> ApiMember:
    return {
        "id": index,
        "user_id": index,
        "name": nation,
        "picture": None,
        "is_current_user": is_current_user,
        "is_bot": is_current_user,
        "commitment": None,
        "nation": nation,
        "eliminated": False,
        "kicked": False,
        "is_game_creator": False,
        "nmr_extensions_remaining": 0,
        "civil_disorder": False,
        "seeking_replacement": False,
        "replaceable": False,
        "removable": False,
    }


def _lookup(variant: ApiVariant) -> dict[str, ApiVariantProvince]:
    return {province["id"]: province for province in variant["provinces"]}


def _resolve(lookup: dict[str, ApiVariantProvince], province_id: str) -> ApiVariantProvince:
    province = lookup.get(province_id)
    if province is None:
        raise FixtureError(f"unknown province '{province_id}'")
    return province


def fixture_to_data(fixture: SelectOrdersFixture) -> ApiData:
    variant = load_variant(fixture["variant"])
    lookup = _lookup(variant)

    units = fixture.get("units", [])
    supply_centers = fixture.get("supply_centers", [])
    order_options = fixture.get("order_options", [])

    nations = [fixture["nation"]]
    for unit in units:
        if unit["nation"] not in nations:
            nations.append(unit["nation"])
    for supply_center in supply_centers:
        if supply_center["nation"] not in nations:
            nations.append(supply_center["nation"])

    members = [_member(index, nation, nation == fixture["nation"]) for index, nation in enumerate(nations)]

    api_units: list[ApiUnit] = [
        {
            "type": unit["type"],
            "nation": _nation(unit["nation"]),
            "province": _province(_resolve(lookup, unit["province"])),
            "dislodged": unit.get("dislodged", False),
            "dislodged_from": None,
        }
        for unit in units
    ]

    api_supply_centers: list[ApiSupplyCenter] = [
        {
            "province": _province(_resolve(lookup, supply_center["province"])),
            "nation": _nation(supply_center["nation"]),
        }
        for supply_center in supply_centers
    ]

    api_orders: list[FlatOrderOption] = []
    for option in order_options:
        source = _resolve(lookup, option["source"])
        target_id = option.get("target")
        aux_id = option.get("aux")
        named_coast_id = option.get("named_coast")
        api_orders.append(
            {
                "source": _field(source["id"], source["name"]),
                "order_type": _field(option["order_type"]),
                "target": (None if target_id is None else _field(target_id, _resolve(lookup, target_id)["name"])),
                "aux": (None if aux_id is None else _field(aux_id, _resolve(lookup, aux_id)["name"])),
                "unit_type": _field(option.get("unit_type")),
                "named_coast": (
                    None if named_coast_id is None else _field(named_coast_id, _resolve(lookup, named_coast_id)["name"])
                ),
            }
        )

    phase_states: list[ApiPhaseState] = [
        {
            "id": str(member["id"]),
            "orders_confirmed": False,
            "eliminated": False,
            "orderable_provinces": [],
            "member": member,
            "max_orders": fixture.get("max_orders"),
        }
        for member in members
    ]

    phase = fixture["phase"]
    return {
        "game": {
            "variant_id": variant["id"],
            "current_phase_id": 1,
            "members": members,
        },
        "phase": {
            "season": phase["season"],
            "year": phase["year"],
            "name": f"{phase['season']} {phase['year']}, {phase['type']}",
            "type": phase["type"],
            "units": api_units,
            "supply_centers": api_supply_centers,
        },
        "phase_states": phase_states,
        "orders": api_orders,
        "variant": variant,
    }


def orders_to_options(orders: list[FlatOrderOption]) -> list[OrderOption]:
    options: list[OrderOption] = []
    for option in orders:
        source = option["source"]
        order_type = option["order_type"]
        if source is None or order_type is None:
            continue
        options.append(
            {
                "source": source["id"],
                "order_type": order_type["id"],
                "target": None if option["target"] is None else option["target"]["id"],
                "aux": None if option["aux"] is None else option["aux"]["id"],
                "unit_type": None if option["unit_type"] is None else option["unit_type"]["id"],
                "named_coast": (None if option["named_coast"] is None else option["named_coast"]["id"]),
            }
        )
    return options


def data_to_fixture(data: ApiData, *, fixture_id: str, notes: str = "") -> SelectOrdersFixture:
    game = data["game"]
    phase = data["phase"]

    current = next((member for member in game["members"] if member["is_current_user"]), None)
    if current is None or not current["nation"]:
        raise FixtureError("api data has no current-user nation")

    units = [
        {
            "type": unit["type"],
            "nation": unit["nation"]["name"],
            "province": unit["province"]["id"],
            **({"dislodged": True} if unit["dislodged"] else {}),
        }
        for unit in phase["units"]
    ]

    supply_centers = [
        {"nation": center["nation"]["name"], "province": center["province"]["id"]}
        for center in phase["supply_centers"]
    ]

    order_options = [
        {key: value for key, value in option.items() if value is not None}
        for option in orders_to_options(data["orders"])
    ]

    max_orders = None
    for phase_state in data["phase_states"]:
        if phase_state["member"]["is_current_user"]:
            max_orders = phase_state["max_orders"]
            break

    fixture: SelectOrdersFixture = {
        "id": fixture_id,
        "variant": game["variant_id"],
        "nation": current["nation"],
        "phase": {
            "season": phase["season"],
            "year": phase["year"],
            "type": phase["type"],
        },
        "units": units,
        "supply_centers": supply_centers,
        "order_options": order_options,
    }
    if notes:
        fixture["notes"] = notes
    if max_orders is not None:
        fixture["max_orders"] = max_orders
    return fixture


def data_to_context(data: ApiData) -> Context:
    try:
        return _context(data)
    except (KeyError, TypeError) as e:
        raise ContextError(f"malformed api data: {e!r}") from e


def _context(data: ApiData) -> Context:
    variant = data["variant"]
    phase = data["phase"]

    members: list[Member] = [
        {
            "name": member["name"],
            "nation": member["nation"] or "",
            "is_current_user": member["is_current_user"],
        }
        for member in data["game"]["members"]
    ]

    provinces: list[Province] = [
        {
            "id": province["id"],
            "name": province["name"],
            "type": province["type"],
            "supply_center": province["supply_center"],
            "parent_id": province["parent_id"],
            "adjacencies": [
                Adjacency(to=adjacency["to"], allows=PASS_TO_ALLOWS[adjacency["pass"]])
                for adjacency in province["adjacencies"]
            ],
        }
        for province in variant["provinces"]
    ]

    units: list[Unit] = [
        {
            "type": unit["type"],
            "nation": unit["nation"]["name"],
            "province": unit["province"]["id"],
            "dislodged": unit["dislodged"],
        }
        for unit in phase["units"]
    ]

    owners = {center["province"]["id"]: center["nation"]["name"] for center in phase["supply_centers"]}
    supply_centers: list[SupplyCenter] = [
        {"nation": owners.get(province["id"]), "province": province["id"]}
        for province in variant["provinces"]
        if province["supply_center"]
    ]

    order_options = orders_to_options(data["orders"])

    max_orders = None
    for phase_state in data["phase_states"]:
        if phase_state["member"]["is_current_user"]:
            max_orders = phase_state["max_orders"]
            break

    channels: list[Channel] = [
        {
            "id": channel["id"],
            "name": channel["name"],
            "private": channel["private"],
            "messages": [
                {
                    "sender": ((message["sender"].get("nation") or {}).get("name")) or "user",
                    "body": message["body"],
                }
                for message in channel["messages"]
            ],
        }
        for channel in data.get("channels", [])
    ]

    return {
        "members": members,
        "phase": {
            "season": phase["season"],
            "year": phase["year"],
            "type": phase["type"],
        },
        "max_orders": max_orders,
        "provinces": provinces,
        "units": units,
        "supply_centers": supply_centers,
        "order_options": order_options,
        "channels": channels,
    }


def fixture_to_context(fixture: SelectOrdersFixture) -> Context:
    return data_to_context(fixture_to_data(fixture))
