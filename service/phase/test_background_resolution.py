from datetime import time, timedelta
from unittest.mock import patch

import pytest
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from common.constants import DeadlineMode, PhaseFrequency, PhaseStatus
from game.models import Game
from phase.models import Phase
from phase.serializers import PhaseStateSerializer


def _resolve_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "phase.resolve_phase"]


def _immediate_resolve_jobs(connector):
    return [j for j in _resolve_jobs(connector) if j["scheduled_at"] is None]


class TestConfirmTrigger:

    @pytest.mark.django_db
    def test_confirm_defers_resolve_phase_task(
        self, authenticated_client, active_game_with_phase_state, in_memory_procrastinate
    ):
        game = active_game_with_phase_state
        phase = game.current_phase

        url = reverse("game-confirm-phase", args=[game.id])
        response = authenticated_client.put(url)

        assert response.status_code == status.HTTP_200_OK
        jobs = _immediate_resolve_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["args"] == {"phase_id": phase.id}
        assert jobs[0]["lock"] == f"resolve-game-{game.id}"

    @pytest.mark.django_db
    def test_unconfirm_does_not_defer(
        self, authenticated_client, active_game_with_confirmed_phase_state, in_memory_procrastinate
    ):
        game = active_game_with_confirmed_phase_state

        url = reverse("game-confirm-phase", args=[game.id])
        response = authenticated_client.put(url)

        assert response.status_code == status.HTTP_200_OK
        assert _immediate_resolve_jobs(in_memory_procrastinate) == []

    @pytest.mark.django_db
    def test_confirm_enqueue_is_atomic_with_write(self, active_game_with_phase_state):
        from procrastinate.contrib.django.models import ProcrastinateJob

        phase = active_game_with_phase_state.current_phase
        phase_state = phase.phase_states.first()
        jobs_before = ProcrastinateJob.objects.count()

        with pytest.raises(RuntimeError):
            with transaction.atomic():
                PhaseStateSerializer().update(phase_state, {})
                assert ProcrastinateJob.objects.count() == jobs_before + 1
                raise RuntimeError("force rollback")

        phase_state.refresh_from_db()
        assert phase_state.orders_confirmed is False
        assert ProcrastinateJob.objects.count() == jobs_before


class TestResolveIfDue:

    @pytest.mark.django_db
    def test_resolves_due_phase(self, phase_factory, classical_england_nation):
        phase = phase_factory(
            scheduled_resolution=timezone.now() - timedelta(hours=1),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        with patch.object(Phase.objects, "resolve", return_value="resolved") as mock_resolve:
            result = Phase.objects.resolve_if_due(phase.id)

        assert result == "resolved"
        mock_resolve.assert_called_once()
        assert mock_resolve.call_args[0][0].id == phase.id

    @pytest.mark.django_db
    def test_skips_not_due_phase(self, phase_factory, classical_england_nation):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        with patch.object(Phase.objects, "resolve") as mock_resolve:
            result = Phase.objects.resolve_if_due(phase.id)

        assert result is None
        mock_resolve.assert_not_called()

    @pytest.mark.django_db
    def test_skips_already_completed_phase(self, phase_factory, classical_england_nation):
        phase = phase_factory(
            scheduled_resolution=timezone.now() - timedelta(hours=1),
            status=PhaseStatus.COMPLETED,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        with patch.object(Phase.objects, "resolve") as mock_resolve:
            result = Phase.objects.resolve_if_due(phase.id)

        assert result is None
        mock_resolve.assert_not_called()

    @pytest.mark.django_db
    def test_missing_phase_is_noop(self):
        with patch.object(Phase.objects, "resolve") as mock_resolve:
            result = Phase.objects.resolve_if_due(999999)

        assert result is None
        mock_resolve.assert_not_called()


class TestDeadlineTimerArming:

    @pytest.mark.django_db
    def test_active_future_deadline_arms_timer(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        future = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=future,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        jobs = [j for j in _resolve_jobs(in_memory_procrastinate) if j["scheduled_at"] is not None]
        assert len(jobs) == 1
        assert jobs[0]["args"] == {"phase_id": phase.id}
        assert jobs[0]["lock"] == f"resolve-game-{phase.game_id}"

    @pytest.mark.django_db
    def test_pending_phase_does_not_arm(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            status=PhaseStatus.PENDING,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        assert _resolve_jobs(in_memory_procrastinate) == []

    @pytest.mark.django_db
    def test_past_deadline_does_not_arm(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        phase_factory(
            scheduled_resolution=timezone.now() - timedelta(hours=1),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        assert _resolve_jobs(in_memory_procrastinate) == []

    @pytest.mark.django_db
    def test_deadline_change_rearms_timer(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        future = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=future,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        phase.scheduled_resolution = future + timedelta(hours=2)
        phase.save()

        assert len(_resolve_jobs(in_memory_procrastinate)) == 2

    @pytest.mark.django_db
    def test_unchanged_deadline_does_not_rearm(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        future = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=future,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        phase.save()

        assert len(_resolve_jobs(in_memory_procrastinate)) == 1


class TestSweepCanary:

    @pytest.mark.django_db
    def test_canary_fires_when_overdue_beyond_grace(self, phase_factory, classical_england_nation):
        phase = phase_factory(
            scheduled_resolution=timezone.now() - timedelta(seconds=400),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        with patch("phase.models.sentry_sdk.capture_message") as mock_capture, patch.object(
            Phase.objects, "resolve", return_value="resolved"
        ) as mock_resolve:
            Phase.objects.sweep_due_phases()

        mock_capture.assert_called_once()
        assert str(phase.id) in mock_capture.call_args[0][0]
        mock_resolve.assert_called_once()

    @pytest.mark.django_db
    def test_no_canary_within_grace(self, phase_factory, classical_england_nation):
        phase_factory(
            scheduled_resolution=timezone.now() - timedelta(seconds=60),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        with patch("phase.models.sentry_sdk.capture_message") as mock_capture, patch.object(
            Phase.objects, "resolve", return_value="resolved"
        ) as mock_resolve:
            Phase.objects.sweep_due_phases()

        mock_capture.assert_not_called()
        mock_resolve.assert_called_once()


class TestFixedTimeEarlyResolution:

    @pytest.mark.django_db
    def test_fixed_time_phase_is_due_when_all_confirmed(self, phase_factory, classical_england_nation, classical_variant):
        game = Game.objects.create(
            variant=classical_variant,
            name="Fixed Time Test",
            status="active",
            deadline_mode=DeadlineMode.FIXED_TIME,
            movement_frequency=PhaseFrequency.DAILY,
            fixed_deadline_time=time(21, 0),
            fixed_deadline_timezone="UTC",
        )
        phase_factory(
            game=game,
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
            ],
        )

        assert Phase.objects.filter_due_phases().filter(game=game).exists()

    @pytest.mark.django_db
    def test_fixed_time_phase_not_due_when_not_all_confirmed(self, phase_factory, classical_england_nation, classical_variant):
        game = Game.objects.create(
            variant=classical_variant,
            name="Fixed Time Test",
            status="active",
            deadline_mode=DeadlineMode.FIXED_TIME,
            movement_frequency=PhaseFrequency.DAILY,
            fixed_deadline_time=time(21, 0),
            fixed_deadline_timezone="UTC",
        )
        phase = phase_factory(
            game=game,
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        assert not Phase.objects.filter_due_phases().filter(pk=phase.id).exists()
