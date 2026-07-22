REGISTRY = {}


def register(event_type):
    def decorator(spec_class):
        REGISTRY[event_type] = spec_class
        return spec_class

    return decorator
