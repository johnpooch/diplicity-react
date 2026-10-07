OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "choices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "option_id": {"type": "string"},
                },
                "required": ["option_id"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["reasoning", "choices"],
    "additionalProperties": False,
}

FIXTURE_SCHEMA_VERSION = 2

_STRING_OR_NULL = {"type": ["string", "null"]}

_PHASE = {
    "type": "object",
    "properties": {
        "season": {"type": "string"},
        "year": {"type": "integer"},
        "type": {"enum": ["Movement", "Retreat", "Adjustment"]},
    },
    "required": ["season", "year", "type"],
    "additionalProperties": False,
}

_UNIT = {
    "type": "object",
    "properties": {
        "type": {"enum": ["Army", "Fleet"]},
        "nation": {"type": "string"},
        "province": {"type": "string"},
        "dislodged": {"type": "boolean"},
        "dislodged_from": {"type": "string"},
    },
    "required": ["type", "nation", "province"],
    "additionalProperties": False,
}

_SUPPLY_CENTER = {
    "type": "object",
    "properties": {
        "nation": {"type": "string"},
        "province": {"type": "string"},
    },
    "required": ["nation", "province"],
    "additionalProperties": False,
}

_OPTION = {
    "type": "object",
    "properties": {
        "source": {"type": "string"},
        "order_type": {"type": "string"},
        "target": _STRING_OR_NULL,
        "aux": _STRING_OR_NULL,
        "unit_type": _STRING_OR_NULL,
        "named_coast": _STRING_OR_NULL,
    },
    "required": ["source", "order_type"],
    "additionalProperties": False,
}

_OPTIONS = {"type": "array", "items": _OPTION}

_RESOLUTION = {
    "type": "object",
    "properties": {
        "nation": {"type": "string"},
        "source": {"type": "string"},
        "result": {"type": "string"},
    },
    "required": ["nation", "source", "result"],
    "additionalProperties": False,
}

_OUTCOME = {
    "type": "object",
    "properties": {
        "resolutions": {"type": "array", "items": _RESOLUTION},
        "units": {"type": "array", "items": _UNIT},
        "supply_centers": {"type": "array", "items": _SUPPLY_CENTER},
    },
    "required": ["resolutions", "units", "supply_centers"],
    "additionalProperties": False,
}

_PROVENANCE = {
    "type": "object",
    "properties": {
        "source": {"enum": ["harvested", "handbuilt"]},
        "game_id": {"type": "string"},
        "phase_id": {"type": "integer"},
        "phase_ordinal": {"type": "integer"},
        "harvested_at": {"type": "string"},
        "press_type": {"type": "string"},
        "was_bot": {"type": "boolean"},
    },
    "required": ["source"],
    "additionalProperties": False,
    "if": {"properties": {"source": {"const": "harvested"}}},
    "then": {"required": ["game_id", "phase_id", "phase_ordinal", "harvested_at", "press_type", "was_bot"]},
}

_OPTION_LABEL = {
    "type": "object",
    "properties": {
        "options": {"type": "array", "items": {"type": "string"}, "minItems": 1, "uniqueItems": True},
        "label": {"enum": ["reasonable", "unreasonable"]},
        "labeller": {"type": "string"},
        "labelled_at": {"type": "string"},
        "note": {"type": "string"},
    },
    "required": ["options", "label", "labeller", "labelled_at"],
    "additionalProperties": False,
}

_ORDER_SET_LABEL = {
    "type": "object",
    "properties": {
        "orders": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
        "label": {"enum": ["reasonable", "unreasonable"]},
        "labeller": {"type": "string"},
        "labelled_at": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["orders", "label", "labeller", "labelled_at"],
    "additionalProperties": False,
}

_DISCARDED = {
    "type": "object",
    "properties": {
        "by": {"type": "string"},
        "at": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["by", "at", "reason"],
    "additionalProperties": False,
}

FIXTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "schema_version": {"const": FIXTURE_SCHEMA_VERSION},
        "id": {"type": "string"},
        "provenance": _PROVENANCE,
        "notes": {"type": "string"},
        "variant": {"type": "string"},
        "nation": {"type": "string"},
        "phase": _PHASE,
        "units": {"type": "array", "items": _UNIT},
        "supply_centers": {"type": "array", "items": _SUPPLY_CENTER},
        "contested_provinces": {"type": "array", "items": {"type": "string"}},
        "order_options": _OPTIONS,
        "max_orders": {"type": ["integer", "null"]},
        "decision_richness": {"type": "integer"},
        "actual_orders": {"type": "object", "additionalProperties": _OPTIONS},
        "actual_outcome": _OUTCOME,
        "ranked_options": {
            "type": "object",
            "properties": {"good": _OPTIONS, "neutral": _OPTIONS, "bad": _OPTIONS},
            "required": ["good", "neutral", "bad"],
            "additionalProperties": False,
        },
        "option_labels": {"type": "array", "items": _OPTION_LABEL},
        "order_set_labels": {"type": "array", "items": _ORDER_SET_LABEL},
        "eval_sets": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
        "discarded": _DISCARDED,
    },
    "required": ["schema_version", "id", "provenance", "variant", "nation", "phase", "eval_sets"],
    "additionalProperties": False,
    "if": {"properties": {"provenance": {"properties": {"source": {"const": "harvested"}}}}},
    "then": {
        "required": [
            "units",
            "supply_centers",
            "order_options",
            "decision_richness",
            "actual_orders",
            "actual_outcome",
        ]
    },
}
