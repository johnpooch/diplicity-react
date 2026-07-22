REGISTRY = {}


def register(event_type):
    def decorator(spec_class):
        spec_class.event_type = event_type
        REGISTRY[event_type] = spec_class
        return spec_class

    return decorator
