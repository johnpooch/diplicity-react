from .checks import ALLOWED


class Refused(Exception):
    def __init__(self, decision):
        super().__init__(decision.reason)
        self.decision = decision


class Policy:
    checks = ()

    @classmethod
    def decide(cls, instance, actor):
        for check in cls.checks:
            decision = check.decide(instance, actor)
            if not decision:
                return decision
        return ALLOWED

    @classmethod
    def reasons(cls):
        return set().union(*(check.reasons() for check in cls.checks))
