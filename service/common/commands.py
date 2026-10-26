import inspect
from functools import reduce, wraps

from django.db import models, transaction

from .actors import SYSTEM
from .policies import Refused


def select_for_update(instance):
    return type(instance)._default_manager.select_for_update().get(pk=instance.pk)


MAX_PROPERTY_LOCKS = 3


def lock_rows(model, value, paths):
    target = value if isinstance(value, models.Model) else model._default_manager.get(pk=value)
    related = {}
    for path in paths:
        row = reduce(getattr, path.split("."), target)
        related[path] = None if row is None else select_for_update(row)
    target = select_for_update(target)
    for path, row in related.items():
        *parents, attribute = path.split(".")
        parent = reduce(getattr, parents, target)
        if isinstance(getattr(type(parent), attribute, None), property):
            confirm_property_lock(parent, attribute, row)
        elif row is not None:
            setattr(parent, attribute, row)
    return target


def confirm_property_lock(parent, attribute, row):
    for _ in range(MAX_PROPERTY_LOCKS):
        current = getattr(parent, attribute)
        if current == row:
            return
        row = None if current is None else select_for_update(current)
    raise RuntimeError(f"{attribute} kept changing while it was being locked")


def command(requires=None, only_if=None, locks=()):
    def decorate(method):
        signature = inspect.signature(method)
        first = list(signature.parameters)[1]
        target_name = None if first == "actor" else first

        @wraps(method)
        def run(manager, *args, **kwargs):
            arguments = signature.bind(manager, *args, **kwargs)
            actor = arguments.arguments.get("actor", SYSTEM)
            with transaction.atomic():
                instance = None
                if target_name is not None:
                    instance = lock_rows(manager.model, arguments.arguments[target_name], locks)
                    arguments.arguments[target_name] = instance
                if only_if is not None and not only_if.decide(instance, actor):
                    return None
                if requires is not None:
                    decision = requires.decide(instance, actor)
                    if not decision:
                        raise Refused(decision)
                return method(*arguments.args, **arguments.kwargs)

        run.policy = requires
        return run

    return decorate
