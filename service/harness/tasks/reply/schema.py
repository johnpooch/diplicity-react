REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["reasoning", "message"],
    "additionalProperties": False,
}
