from dataclasses import dataclass
from typing import Protocol


@dataclass
class InferenceResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


class InferenceClient(Protocol):
    def complete(
        self, *, model, system, messages, output_schema=None, max_tokens=None
    ) -> InferenceResult: ...
