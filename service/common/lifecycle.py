from django.utils import timezone

from common.policies import ALLOW, deny


class TransitionNotAllowed(Exception):
    def __init__(self, decision):
        super().__init__(decision.reason)
        self.decision = decision


class BoundTransition:
    def __init__(self, transition, instance):
        self.transition = transition
        self.instance = instance

    def available(self):
        return self.transition.available(self.instance)

    def __call__(self, *args, **kwargs):
        return self.transition.run(self.instance, *args, **kwargs)


class Transition:
    def __init__(self, method, source, target, guard, stamp, reason):
        self.method = method
        self.source = source
        self.target = target
        self.guard = guard
        self.stamp = stamp
        self.reason = reason

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundTransition(self, instance)

    def available(self, instance):
        if self.source is not None and instance.status not in self.source:
            return deny(self.reason)
        if self.guard is not None:
            decision = self.guard(instance)
            if not decision:
                return decision
        return ALLOW

    def run(self, instance, *args, **kwargs):
        decision = self.available(instance)
        if not decision:
            raise TransitionNotAllowed(decision)
        fields = [field.attname for field in instance._meta.concrete_fields if not field.primary_key]
        before = {name: getattr(instance, name) for name in fields}
        result = self.method(instance, *args, **kwargs)
        if self.target is not None:
            instance.status = self.target
        if self.stamp is not None:
            setattr(instance, self.stamp, timezone.now())
        changed = [name for name in fields if getattr(instance, name) != before[name]]
        if changed:
            instance.save(update_fields=sorted(set(changed) | {"updated_at"}))
        return result


def transition(source=None, target=None, guard=None, stamp=None, reason=None):
    sources = (source,) if isinstance(source, str) else source

    def decorator(method):
        return Transition(method, sources, target, guard, stamp, reason)

    return decorator
