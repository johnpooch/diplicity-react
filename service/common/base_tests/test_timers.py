from datetime import timedelta

import pytest
from django.utils import timezone

from common.timers import NOW, Timer
from game_spike.factories import GameFactory

pytestmark = pytest.mark.django_db


class AlarmTimer(Timer):
    task = "game_spike.start_if_mustered"
    job_id_field = "muster_job_id"
    live_statuses = ("todo",)
    eligible = "all"
    argument = "game_id"

    def __init__(self, when):
        self.when = when

    def run_at(self, game):
        return self.when


class IneligibleAlarmTimer(AlarmTimer):
    eligible = "none"


def _job(connector, job_id):
    return connector.jobs[job_id]


@pytest.fixture
def connector(in_memory_procrastinate):
    return in_memory_procrastinate


class TestTimer:
    def test_schedules_job_and_stores_its_id(self, connector):
        game = GameFactory()
        when = timezone.now() + timedelta(hours=1)
        job_id = AlarmTimer(when).sync(game)
        assert game.muster_job_id == job_id
        assert _job(connector, job_id)["scheduled_at"] == when
        assert _job(connector, job_id)["args"] == {"game_id": game.pk}

    def test_keeps_live_job_scheduled_for_same_time(self, connector):
        game = GameFactory()
        when = timezone.now() + timedelta(hours=1)
        first = AlarmTimer(when).sync(game)
        assert AlarmTimer(when).sync(game) == first

    def test_replaces_job_when_time_changes(self, connector):
        game = GameFactory()
        first = AlarmTimer(timezone.now() + timedelta(hours=1)).sync(game)
        second = AlarmTimer(timezone.now() + timedelta(hours=2)).sync(game)
        assert second != first
        assert _job(connector, first)["status"] == "cancelled"

    def test_cancels_job_when_none_should_exist(self, connector):
        game = GameFactory()
        first = AlarmTimer(timezone.now() + timedelta(hours=1)).sync(game)
        assert AlarmTimer(None).sync(game) is None
        assert game.muster_job_id is None
        assert _job(connector, first)["status"] == "cancelled"

    def test_cancels_job_when_row_is_ineligible(self, connector):
        game = GameFactory()
        first = AlarmTimer(timezone.now() + timedelta(hours=1)).sync(game)
        assert IneligibleAlarmTimer(timezone.now() + timedelta(hours=1)).sync(game) is None
        assert _job(connector, first)["status"] == "cancelled"

    def test_now_schedules_job_to_run_immediately(self, connector):
        game = GameFactory()
        job_id = AlarmTimer(NOW).sync(game)
        assert _job(connector, job_id)["scheduled_at"] is None

    def test_keeps_immediate_job_when_still_due_now(self, connector):
        game = GameFactory()
        first = AlarmTimer(NOW).sync(game)
        assert AlarmTimer(NOW).sync(game) == first

    def test_replaces_job_that_is_no_longer_live(self, connector):
        game = GameFactory()
        when = timezone.now() + timedelta(hours=1)
        first = AlarmTimer(when).sync(game)
        connector.jobs[first]["status"] = "succeeded"
        assert AlarmTimer(when).sync(game) != first
