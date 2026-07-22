from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmitContext:
    event_type: str
    game: object = None
    phase: object = None
    actor: object = None
    channel: object = None
    payload: dict = field(default_factory=dict)


def build_context(event_type, game=None, phase=None, actor=None, channel=None, payload=None):
    if game is None and phase is not None:
        game = phase.game
    return EmitContext(event_type, game, phase, actor, channel, payload or {})
