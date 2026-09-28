import json
from pathlib import Path

from jsonschema import Draft202012Validator

from select_orders.exceptions import FixtureError
from select_orders.options import OPTION_KEYS, option_id
from select_orders.schema import FIXTURE_SCHEMA
from select_orders.types import Fixture, FixtureOrderOption, OrderOption, RankedOptions

_VALIDATOR = Draft202012Validator(FIXTURE_SCHEMA)


def validate_fixture(fixture: Fixture) -> Fixture:
    error = next(iter(sorted(_VALIDATOR.iter_errors(fixture), key=lambda e: list(e.absolute_path))), None)
    if error is not None:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise FixtureError(f"fixture '{fixture.get('id', '?')}' violates schema at {location}: {error.message}")
    return fixture


def read_fixture(path: Path) -> Fixture:
    return validate_fixture(json.loads(path.read_text()))


def write_fixture(path: Path, fixture: Fixture) -> None:
    path.write_text(json.dumps(validate_fixture(fixture), indent=2) + "\n")


def full_option(option: FixtureOrderOption) -> OrderOption:
    return {key: option.get(key) for key in OPTION_KEYS}


def foreign_orders(fixture: Fixture) -> list[OrderOption] | None:
    actual = fixture.get("actual_orders")
    if actual is None:
        return None
    return [full_option(order) for nation, orders in actual.items() if nation != fixture["nation"] for order in orders]


def ranked_options(fixture: Fixture) -> RankedOptions | None:
    if "ranked_options" in fixture:
        return fixture["ranked_options"]
    labels = fixture.get("option_labels", [])
    if not labels:
        return None
    options = {option_id(full_option(option)): option for option in fixture.get("order_options", [])}
    ranked: RankedOptions = {"good": [], "neutral": [], "bad": []}
    for entry in labels:
        unknown = [labelled for labelled in entry["options"] if labelled not in options]
        if unknown:
            raise FixtureError(f"fixture '{fixture['id']}' labels unknown option id(s) {unknown}")
        if len(entry["options"]) == 1:
            ranked["good" if entry["label"] == "reasonable" else "bad"].append(options[entry["options"][0]])
    return ranked
