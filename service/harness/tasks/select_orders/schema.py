ORDER_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "choices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_id": {"type": "string"},
                    "option_index": {"type": "integer"},
                },
                "required": ["source_id", "option_index"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["reasoning", "choices"],
    "additionalProperties": False,
}
