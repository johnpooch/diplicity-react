from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmitContext:
    event_type: str
    game: object = None
    phase: object = None
    actor: object = None
    channel: object = None
    payload: dict = field(default_factory=dict)


def build_context(event_type, game=None, phase=None, actor=None, channel=None, message=None, draw_proposal=None, **payload):
    if message is not None:
        game = message.channel.game
        phase = message.phase or game.phases.last()
        actor = message.sender.user
        channel = message.channel
        payload["body"] = message.body
    elif draw_proposal is not None:
        game = draw_proposal.game
        phase = draw_proposal.phase
        actor = draw_proposal.created_by.user
    elif phase is not None and game is None:
        game = phase.game
    return EmitContext(event_type, game, phase, actor, channel, payload)
