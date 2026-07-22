from emit.registry import REGISTRY


def _spec(event_type):
    return REGISTRY[event_type]()


def recipients(event_type, **kwargs):
    # Resolves the audience without delivering; intended for direct use by tests only.
    # Production code should call emit(), which is why this is not exported from the package.
    spec = _spec(event_type)
    return spec.get_recipients(spec.build_context(**kwargs))


def emit(event_type, **kwargs):
    spec = _spec(event_type)
    ctx = spec.build_context(**kwargs)
    recipient_ids = spec.get_recipients(ctx)
    for transport in spec.transports:
        transport().deliver(spec, ctx, recipient_ids)
