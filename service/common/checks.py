from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str | None = None

    def __bool__(self):
        return self.allowed


ALLOWED = Decision(True)


class Check:
    reason = None

    @classmethod
    def decide(cls, instance, actor):
        if cls().check(instance, actor):
            return ALLOWED
        return Decision(False, cls.reason)

    @classmethod
    def reasons(cls):
        return {cls.reason} - {None}

    def check(self, instance, actor):
        raise NotImplementedError
