import json
from pathlib import Path

from adjudicator import adjudicate
from adjudicator.options import get_options
from adjudicator.serializers import deserialize_game_state, deserialize_variant, serialize_options

from engine.exceptions import UnknownVariantError

VARIANTS_DIR = Path(__file__).resolve().parent.parent / "data" / "variants"


def load_variant(variant_id: str) -> dict:
    path = VARIANTS_DIR / f"{variant_id}.canonical.json"
    if not path.exists():
        raise UnknownVariantError(f"unknown variant '{variant_id}'")
    return json.loads(path.read_text())


def legal_options(variant: dict, game_state: dict) -> list[dict]:
    state = deserialize_game_state(game_state, deserialize_variant(variant))
    return serialize_options(get_options(state))


def resolve(variant: dict, game_state: dict) -> list[dict]:
    return adjudicate(variant, game_state)
