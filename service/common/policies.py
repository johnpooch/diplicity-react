from dataclasses import dataclass

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str | None = None

    def __bool__(self):
        return self.allowed


ALLOW = Decision(True)


def deny(reason=None):
    return Decision(False, reason)


class Denied(PermissionDenied):
    def __init__(self, decision):
        super().__init__(
            detail=decision.reason or self.default_detail,
            code=decision.reason or self.default_code,
        )
        self.decision = decision


def allows(decision):
    class Allows(BasePermission):
        def has_permission(self, request, view):
            return True

        def has_object_permission(self, request, view, obj):
            result = getattr(obj, decision)(request.user)
            if not result:
                raise Denied(result)
            return True

    Allows.__name__ = f"Allows[{decision}]"
    Allows.__qualname__ = Allows.__name__
    return Allows
