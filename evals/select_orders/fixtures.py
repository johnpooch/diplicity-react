import json
from pathlib import Path

from jsonschema import Draft202012Validator

from select_orders.exceptions import FixtureError
from select_orders.options import OPTION_KEYS
from select_orders.schema import FIXTURE_SCHEMA
from select_orders.types import Fixture, FixtureOrderOption, OrderOption

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
