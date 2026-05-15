from __future__ import annotations

from typing import Any, Dict, List

from .engine import Engine as _Engine
from .serializers import (
    deserialize_game_state as _deserialize_game_state,
    deserialize_variant as _deserialize_variant,
    serialize_game_state as _serialize_game_state,
)


__all__ = ["adjudicate"]


def adjudicate(variant: Dict[str, Any], game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    parsed_variant = _deserialize_variant(variant)
    state = _deserialize_game_state(game_state, parsed_variant)
    new_states = _Engine().adjudicate(state)
    return [_serialize_game_state(s) for s in new_states]


for _name in ("engine", "serializers", "domain"):
    globals().pop(_name, None)
del _name
