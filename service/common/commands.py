from django.db import transaction

from common.policies import Denied
from emit import emit


class Command:
    decision = None
    events = ()

    def __init__(self, actor=None, **data):
        self.actor = actor
        self.data = data

    def __call__(self, target=None):
        with transaction.atomic():
            if target is not None:
                target = self.lock(target)
                if target is None or not self.applies(target):
                    return None
                self.check(target)
            instance = self.perform(target)
            for event in self.events_for(instance):
                emit(event, **self.event_kwargs(event, instance))
            return instance

    def lock(self, target):
        return type(target).objects.select_for_update().filter(pk=target.pk).first()

    def applies(self, target):
        return True

    def check(self, target):
        if self.decision is None:
            return
        decision = getattr(target, self.decision)(self.actor)
        if not decision:
            raise Denied(decision)

    def perform(self, target):
        raise NotImplementedError

    def events_for(self, instance):
        return self.events

    def event_kwargs(self, event, instance):
        return {"actor": self.actor}
