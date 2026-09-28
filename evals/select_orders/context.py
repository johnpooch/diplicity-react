import json
from pathlib import Path

from select_orders.exceptions import FixtureError
from select_orders.types import Context, Fixture

VARIANTS_DIR = Path(__file__).resolve().parent.parent / "data" / "variants"

PASS_TO_ALLOWS = {
    "army": ["army"],
    "fleet": ["fleet"],
    "both": ["army", "fleet"],
}


def load_variant(variant_id: str) -> dict:
    path = VARIANTS_DIR / f"{variant_id}.json"
    if not path.exists():
        raise FixtureError(f"unknown variant '{variant_id}'")
    return json.loads(path.read_text())


def _check_province(province_ids: set[str], province_id: str | None) -> str | None:
    if province_id is not None and province_id not in province_ids:
        raise FixtureError(f"unknown province '{province_id}'")
    return province_id


def fixture_to_context(fixture: Fixture) -> Context:
    variant = load_variant(fixture["variant"])
    province_ids = {province["id"] for province in variant["provinces"]}

    units = fixture.get("units", [])
    supply_centers = fixture.get("supply_centers", [])

    nations = [fixture["nation"]]
    for entry in [*units, *supply_centers]:
        if entry["nation"] not in nations:
            nations.append(entry["nation"])

    owners = {_check_province(province_ids, center["province"]): center["nation"] for center in supply_centers}

    return {
        "members": [
            {"name": nation, "nation": nation, "is_current_user": nation == fixture["nation"]} for nation in nations
        ],
        "phase": {
            "season": fixture["phase"]["season"],
            "year": fixture["phase"]["year"],
            "type": fixture["phase"]["type"],
        },
        "max_orders": fixture.get("max_orders"),
        "provinces": [
            {
                "id": province["id"],
                "name": province["name"],
                "type": province["type"],
                "supply_center": province["supply_center"],
                "parent_id": province["parent_id"],
                "adjacencies": [
                    {"to": adjacency["to"], "allows": PASS_TO_ALLOWS[adjacency["pass"]]}
                    for adjacency in province["adjacencies"]
                ],
            }
            for province in variant["provinces"]
        ],
        "units": [
            {
                "type": unit["type"],
                "nation": unit["nation"],
                "province": _check_province(province_ids, unit["province"]),
                "dislodged": unit.get("dislodged", False),
            }
            for unit in units
        ],
        "supply_centers": [
            {"nation": owners.get(province["id"]), "province": province["id"]}
            for province in variant["provinces"]
            if province["supply_center"]
        ],
        "order_options": [
            {
                "source": _check_province(province_ids, option["source"]),
                "order_type": option["order_type"],
                "target": _check_province(province_ids, option.get("target")),
                "aux": _check_province(province_ids, option.get("aux")),
                "unit_type": option.get("unit_type"),
                "named_coast": _check_province(province_ids, option.get("named_coast")),
            }
            for option in fixture.get("order_options", [])
        ],
    }
