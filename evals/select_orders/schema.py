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
