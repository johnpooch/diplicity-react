import json
from pathlib import Path

from jsonschema import Draft202012Validator

from harvest.exceptions import HarvestError

_STRING_OR_NULL = {"type": ["string", "null"]}


def _rows(properties):
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
    }


SNAPSHOT_SCHEMA = {
    "type": "object",
    "properties": {
        "games": _rows(
            {
                "id": {"type": "string"},
                "variant": {"type": "string"},
                "press_type": {"type": "string"},
                "status": {"type": "string"},
            }
        ),
        "phases": _rows(
            {
                "id": {"type": "integer"},
                "game": {"type": "string"},
                "ordinal": {"type": "integer"},
                "season": {"type": "string"},
                "year": {"type": "integer"},
                "type": {"type": "string"},
                "status": {"type": "string"},
                "contested_provinces": {"type": "array", "items": {"type": "string"}},
            }
        ),
        "units": _rows(
            {
                "phase": {"type": "integer"},
                "province": {"type": "string"},
                "type": {"type": "string"},
                "nation": {"type": "string"},
                "dislodged": {"type": "boolean"},
                "dislodged_from": _STRING_OR_NULL,
            }
        ),
        "supply_centers": _rows(
            {
                "phase": {"type": "integer"},
                "province": {"type": "string"},
                "nation": {"type": "string"},
            }
        ),
        "orders": _rows(
            {
                "phase": {"type": "integer"},
                "nation": {"type": "string"},
                "order_type": {"type": "string"},
                "source": {"type": "string"},
                "target": _STRING_OR_NULL,
                "aux": _STRING_OR_NULL,
                "unit_type": _STRING_OR_NULL,
                "named_coast": _STRING_OR_NULL,
                "resolution": _STRING_OR_NULL,
            }
        ),
        "players": _rows(
            {
                "phase": {"type": "integer"},
                "nation": {"type": "string"},
                "was_bot": {"type": "boolean"},
            }
        ),
    },
    "required": ["games", "phases", "units", "supply_centers", "orders", "players"],
    "additionalProperties": False,
}

_VALIDATOR = Draft202012Validator(SNAPSHOT_SCHEMA)


def validate_snapshot(snapshot: dict) -> dict:
    error = next(iter(sorted(_VALIDATOR.iter_errors(snapshot), key=lambda e: list(e.absolute_path))), None)
    if error is not None:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise HarvestError(f"snapshot violates schema at {location}: {error.message}")
    return snapshot


def read_snapshot(path: Path) -> dict:
    if not path.exists():
        raise HarvestError(f"no snapshot at {path}")
    return validate_snapshot(json.loads(path.read_text()))
