import pytest

from game_spike.factories import GameFactory
from game_spike.timers import MusterReminderTimer, MusterTimer

pytestmark = pytest.mark.django_db


def _live_jobs(connector, task):
    return [job for job in connector.jobs.values() if job["task_name"] == task and job["status"] == "todo"]


class TestMusterTimers:
    def test_mustering_game_is_started_at_its_deadline(self, procrastinate_jobs):
        game = GameFactory(mustering=True)
        jobs = _live_jobs(procrastinate_jobs, MusterTimer.task)
        assert [(job["args"], job["scheduled_at"]) for job in jobs] == [({"game_id": game.id}, game.muster_deadline)]

    def test_mustering_game_is_reminded_before_its_deadline(self, procrastinate_jobs):
        game = GameFactory(mustering=True)
        jobs = _live_jobs(procrastinate_jobs, MusterReminderTimer.task)
        assert [job["scheduled_at"] for job in jobs] == [game.muster_reminder_at]

    def test_fully_mustered_game_is_started_immediately(self, procrastinate_jobs):
        GameFactory(mustering=True, mustered=True)
        assert [job["scheduled_at"] for job in _live_jobs(procrastinate_jobs, MusterTimer.task)] == [None]

    def test_fully_mustered_game_is_not_reminded(self, procrastinate_jobs):
        GameFactory(mustering=True, mustered=True)
        assert _live_jobs(procrastinate_jobs, MusterReminderTimer.task) == []

    def test_pending_game_has_no_muster_jobs(self, procrastinate_jobs):
        GameFactory(full=True)
        assert _live_jobs(procrastinate_jobs, MusterTimer.task) == []

    def test_started_game_has_no_muster_jobs(self, procrastinate_jobs):
        GameFactory(mustering=True, started=True)
        assert _live_jobs(procrastinate_jobs, MusterTimer.task) == []
        assert _live_jobs(procrastinate_jobs, MusterReminderTimer.task) == []
