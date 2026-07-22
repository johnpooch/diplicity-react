from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmitContext:
    event_type: str
    game: object = None
    phase: object = None
    actor: object = None
    channel: object = None
    payload: dict = field(default_factory=dict)
