from emit.context import build_context
from emit.registry import REGISTRY


def _spec(event_type):
    return REGISTRY[event_type]()


def recipients(event_type, *, game=None, phase=None, actor=None, channel=None, context=None):
    # Resolves the audience without delivering; intended for direct use by tests only.
    # Production code should call emit(), which is why this is not exported from the package.
    spec = _spec(event_type)
    return spec.get_recipients(build_context(event_type, game, phase, actor, channel, context))


def emit(event_type, *, game=None, phase=None, actor=None, channel=None, context=None):
    spec = _spec(event_type)
    ctx = build_context(event_type, game, phase, actor, channel, context)
    recipient_ids = spec.get_recipients(ctx)
    for transport in spec.transports:
        transport().deliver(spec, ctx, recipient_ids)
