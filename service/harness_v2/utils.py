import json

from harness_v2.exceptions import ContextError, ParsingError
from harness_v2.types import Context


def current_nation(context: Context) -> str:
    for member in context["members"]:
        if member["is_current_user"]:
            return member["nation"]
    raise ContextError("context has no current-user member")


def strip_fences(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_json_object(completion: str) -> dict:
    text = strip_fences(completion)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ParsingError(f"could not parse JSON: {e}") from e
    if not isinstance(data, dict):
        raise ParsingError("response JSON is not an object")
    return data
