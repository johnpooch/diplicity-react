from types import SimpleNamespace

import pytest

from common.lifecycle import TransitionNotAllowed, transition
from common.policies import ALLOW, deny


class Field:
    primary_key = False

    def __init__(self, attname):
        self.attname = attname


def _unlocked(door):
    return deny("door_locked") if door.locked else ALLOW


class Door:
    _meta = SimpleNamespace(
        concrete_fields=[Field(name) for name in ("status", "opened_at", "note", "locked", "updated_at")]
    )

    def __init__(self, status="closed", locked=False):
        self.status = status
        self.opened_at = None
        self.note = ""
        self.locked = locked
        self.updated_at = None
        self.saved_fields = None

    def save(self, update_fields):
        self.saved_fields = update_fields

    @transition(source="closed", target="open", stamp="opened_at", reason="not_closed")
    def open(self, note):
        self.note = note
        return "opened"

    @transition(guard=_unlocked)
    def annotate(self, note):
        self.note = note


class TestTransition:
    def test_sets_target_status_and_stamp(self):
        door = Door()
        door.open("wide")
        assert door.status == "open"
        assert door.opened_at is not None

    def test_returns_method_result(self):
        assert Door().open("wide") == "opened"

    def test_saves_only_changed_fields(self):
        door = Door()
        door.open("wide")
        assert door.saved_fields == ["note", "opened_at", "status", "updated_at"]

    def test_refuses_transition_from_other_source(self):
        with pytest.raises(TransitionNotAllowed) as refused:
            Door(status="open").open("wide")
        assert refused.value.decision.reason == "not_closed"

    def test_reports_availability_as_decision(self):
        assert Door().open.available()
        assert Door(status="open").open.available().reason == "not_closed"

    def test_guard_decides_change_without_status(self):
        door = Door()
        door.annotate("hinge")
        assert door.status == "closed"
        assert door.saved_fields == ["note", "updated_at"]

    def test_failed_guard_refuses_with_its_reason(self):
        with pytest.raises(TransitionNotAllowed) as refused:
            Door(locked=True).annotate("hinge")
        assert refused.value.decision.reason == "door_locked"
