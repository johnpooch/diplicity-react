import json
from typing import ClassVar, Sequence

from harness.blocks.base import Block
from harness.exceptions import ParseError
from harness.types import ContextData


def extract_json(response_text: str) -> dict:
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ParseError(f"could not parse JSON from response: {e}") from e
    if not isinstance(data, dict):
        raise ParseError("response JSON is not an object")
    return data


class TaskDefinition:
    name: ClassVar[str]
    system_prompt: ClassVar[str]
    instruction: ClassVar[str]
    blocks: ClassVar[Sequence[Block]]
    output_schema: ClassVar[dict | None] = None
    max_tokens: ClassVar[int | None] = None

    @classmethod
    def parse(cls, response: str, *, context: ContextData):
        raise NotImplementedError
