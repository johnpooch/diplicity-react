from __future__ import annotations

from typing import Any, Dict, List

from .engine import Engine as _Engine
from .serializers import (
    deserialize_game_state as _deserialize_game_state,
    deserialize_variant as _deserialize_variant,
    serialize_game_state as _serialize_game_state,
    serialize_options as _serialize_options,
)


__all__ = ["adjudicate", "get_options"]


def adjudicate(variant: Dict[str, Any], game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    parsed_variant = _deserialize_variant(variant)
    state = _deserialize_game_state(game_state, parsed_variant)
    new_states = _Engine(parsed_variant).adjudicate(state)
    return [_serialize_game_state(s) for s in new_states]


def get_options(variant: Dict[str, Any], game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    parsed_variant = _deserialize_variant(variant)
    state = _deserialize_game_state(game_state, parsed_variant)
    options = _Engine(parsed_variant).get_options(state)
    return _serialize_options(options)


for _name in ("engine", "serializers", "domain"):
    globals().pop(_name, None)
del _name
