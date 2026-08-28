from datetime import datetime, time, timedelta, timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from procrastinate.contrib.django import app as procrastinate_app
from rest_framework import status

from common.constants import DeadlineMode, GameStatus, PhaseFrequency, PhaseStatus, ResolutionJob
from game.models import Game
from member.models import Member
from phase.models import Phase
from phase.serializers import PhaseStateSerializer
from phase.tasks import resolve_phase


def _resolve_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == ResolutionJob.TASK_NAME]


def _immediate_resolve_jobs(connector):
    return [j for j in _resolve_jobs(connector) if j["scheduled_at"] is None]


def _pending_resolve_jobs(connector):
    return [j for j in _resolve_jobs(connector) if j["status"] == ResolutionJob.TODO]


def _todo_resolve_jobs():
    return procrastinate_app.job_manager.list_jobs(
        task=ResolutionJob.TASK_NAME, status=ResolutionJob.TODO
    )


def _armed_job(phase):
    phase.refresh_from_db()
    if phase.resolution_job_id is None:
        return None
    jobs = procrastinate_app.job_manager.list_jobs(id=phase.resolution_job_id)
    return jobs[0] if jobs else None


def _fetch_job_id():
    with connection.cursor() as cursor:
        cursor.execute("SELECT procrastinate_register_worker_v1()")
        worker_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM procrastinate_fetch_job_v2(NULL, %s)", [worker_id])
        row = cursor.fetchone()
    return row[0] if row else None


def _claim(phase_id):
    return Phase.objects.filter_due_phases().filter(pk=phase_id).update(
        status=PhaseStatus.PROCESSING, processing_started_at=timezone.now()
    )


def _fetchable_job_ids():
    fetched = []
    while True:
        job_id = _fetch_job_id()
        if job_id is None:
            return fetched
        fetched.append(job_id)


class TestConfirmTrigger:

    @pytest.mark.django_db
    def test_confirm_arms_a_phase_with_no_scheduled_resolution(
        self, authenticated_client, active_game_with_phase_state, in_memory_procrastinate
    ):
        game = active_game_with_phase_state
        phase = game.current_phase
        assert phase.scheduled_resolution is None
        assert phase.resolution_job_id is None

        url = reverse("game-confirm-phase", args=[game.id])
        response = authenticated_client.put(url)

        assert response.status_code == status.HTTP_200_OK
        jobs = _immediate_resolve_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["args"] == {"phase_id": phase.id}
        assert jobs[0]["lock"] == ResolutionJob.lock_for_game(game.id)

    @pytest.mark.django_db
    def test_unconfirm_does_not_arm_a_phase_with_no_scheduled_resolution(
        self, authenticated_client, active_game_with_confirmed_phase_state, in_memory_procrastinate
    ):
        game = active_game_with_confirmed_phase_state

        url = reverse("game-confirm-phase", args=[game.id])
        response = authenticated_client.put(url)

        assert response.status_code == status.HTTP_200_OK
        assert _pending_resolve_jobs(in_memory_procrastinate) == []

    @pytest.mark.django_db
    def test_confirming_the_last_outstanding_order_pulls_the_job_forward(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        deadline = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=deadline,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.refresh_from_db()
        deadline_job_id = phase.resolution_job_id
        assert in_memory_procrastinate.jobs[deadline_job_id]["scheduled_at"] == deadline

        PhaseStateSerializer().update(phase.phase_states.first(), {})

        phase.refresh_from_db()
        assert phase.resolution_job_id != deadline_job_id
        assert in_memory_procrastinate.jobs[deadline_job_id]["status"] == "cancelled"
        assert in_memory_procrastinate.jobs[phase.resolution_job_id]["scheduled_at"] is None

    @pytest.mark.django_db
    def test_unconfirming_pushes_the_job_back_to_the_deadline(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        deadline = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=deadline,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
            ],
        )
        Phase.objects.arm_resolution(phase)
        phase.refresh_from_db()
        assert in_memory_procrastinate.jobs[phase.resolution_job_id]["scheduled_at"] is None

        PhaseStateSerializer().update(phase.phase_states.first(), {})

        phase.refresh_from_db()
        assert in_memory_procrastinate.jobs[phase.resolution_job_id]["scheduled_at"] == deadline

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

        with patch.object(Phase.objects, "_resolve_claimed", return_value="resolved") as mock_resolve:
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

        with patch.object(Phase.objects, "_resolve_claimed") as mock_resolve:
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

        with patch.object(Phase.objects, "_resolve_claimed") as mock_resolve:
            result = Phase.objects.resolve_if_due(phase.id)

        assert result is None
        mock_resolve.assert_not_called()

    @pytest.mark.django_db
    def test_missing_phase_is_noop(self):
        with patch.object(Phase.objects, "_resolve_claimed") as mock_resolve:
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
    def test_past_deadline_arms_for_that_past_moment(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        deadline = timezone.now() - timedelta(hours=1)
        phase_factory(
            scheduled_resolution=deadline,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        jobs = _resolve_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["scheduled_at"] == deadline

    @pytest.mark.django_db
    def test_phase_with_no_scheduled_resolution_does_not_arm(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        phase_factory(
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

    @pytest.mark.django_db
    def test_deadline_change_cancels_previous_job(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        future = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=future,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.refresh_from_db()
        old_job_id = phase.resolution_job_id

        phase.scheduled_resolution = future + timedelta(hours=2)
        phase.save()

        assert in_memory_procrastinate.jobs[old_job_id]["status"] == "cancelled"

    @pytest.mark.django_db
    def test_phase_completion_cancels_pending_job(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        future = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=future,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.refresh_from_db()
        old_job_id = phase.resolution_job_id

        phase.status = PhaseStatus.COMPLETED
        phase.save()

        assert in_memory_procrastinate.jobs[old_job_id]["status"] == "cancelled"

    @pytest.mark.django_db
    def test_phase_completion_clears_job_id(
        self, phase_factory, in_memory_procrastinate, classical_england_nation
    ):
        future = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=future,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.refresh_from_db()
        assert phase.resolution_job_id is not None

        phase.status = PhaseStatus.COMPLETED
        phase.save()

        phase.refresh_from_db()
        assert phase.resolution_job_id is None


class TestProcessingStatus:

    @pytest.fixture
    def due_phase(self, phase_factory, classical_england_nation):
        return phase_factory(
            scheduled_resolution=timezone.now() - timedelta(hours=1),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

    @pytest.mark.django_db
    def test_phase_is_processing_before_adjudication_starts(self, due_phase):
        observed = {}

        def record(phase):
            observed["status"] = Phase.objects.values_list("status", flat=True).get(pk=phase.pk)
            return "resolved"

        with patch.object(Phase.objects, "_resolve_claimed", side_effect=record):
            Phase.objects.resolve_if_due(due_phase.id)

        assert observed["status"] == PhaseStatus.PROCESSING

    @pytest.mark.django_db
    def test_claim_records_when_processing_started(self, due_phase):
        before = timezone.now()

        with patch.object(Phase.objects, "_resolve_claimed", return_value="resolved"):
            Phase.objects.resolve_if_due(due_phase.id)

        due_phase.refresh_from_db()
        assert due_phase.processing_started_at >= before

    @pytest.mark.django_db
    def test_claim_is_refused_for_a_phase_another_worker_is_already_processing(self, due_phase):
        Phase.objects.filter(pk=due_phase.pk).update(status=PhaseStatus.PROCESSING)

        with Phase.objects.claim(
            due_phase.pk, Phase.objects.filter(status=PhaseStatus.ACTIVE)
        ) as claimed:
            assert claimed is False

    @pytest.mark.django_db
    def test_failed_resolution_returns_the_phase_to_active(self, due_phase):
        with patch.object(Phase.objects, "_set_orders_outcome", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                Phase.objects.resolve_if_due(due_phase.id)

        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.ACTIVE
        assert due_phase.processing_started_at is None

    @pytest.mark.django_db
    def test_a_processing_phase_is_not_resolved(self, due_phase):
        Phase.objects.filter(pk=due_phase.pk).update(status=PhaseStatus.PROCESSING)

        with patch.object(Phase.objects, "_resolve_claimed") as mock_resolve:
            assert Phase.objects.resolve_if_due(due_phase.id) is None

        mock_resolve.assert_not_called()


class TestFusedClaim:

    @pytest.fixture
    def due_phase(self, phase_factory, classical_england_nation):
        return phase_factory(
            scheduled_resolution=timezone.now() - timedelta(hours=1),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

    @pytest.mark.django_db
    def test_the_claim_is_a_single_query_and_takes_a_due_phase(self, due_phase):
        with CaptureQueriesContext(connection) as queries:
            claimed = _claim(due_phase.id)

        assert claimed == 1
        assert len(queries) == 1
        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.PROCESSING

    @pytest.mark.django_db
    def test_a_paused_game_is_not_claimed(self, due_phase):
        Game.objects.filter(pk=due_phase.game_id).update(paused_at=timezone.now())

        assert _claim(due_phase.id) == 0

        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_a_completed_game_is_not_claimed(self, due_phase):
        Game.objects.filter(pk=due_phase.game_id).update(status=GameStatus.COMPLETED)

        assert _claim(due_phase.id) == 0

        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_an_abandoned_game_is_not_claimed(self, due_phase):
        Game.objects.filter(pk=due_phase.game_id).update(status=GameStatus.ABANDONED)

        assert _claim(due_phase.id) == 0

        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_a_sandbox_game_is_not_claimed(self, due_phase):
        Game.objects.filter(pk=due_phase.game_id).update(sandbox=True)

        assert _claim(due_phase.id) == 0

        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_an_unconfirmed_phase_before_its_deadline_is_not_claimed(
        self, phase_factory, classical_england_nation
    ):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        assert _claim(phase.id) == 0

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_a_phase_already_processing_is_not_claimed(self, due_phase):
        started = timezone.now() - timedelta(seconds=30)
        Phase.objects.filter(pk=due_phase.pk).update(
            status=PhaseStatus.PROCESSING, processing_started_at=started
        )

        assert _claim(due_phase.id) == 0

        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.PROCESSING
        assert due_phase.processing_started_at == started

    @pytest.mark.django_db
    def test_a_phase_that_no_longer_exists_is_not_claimed(self, due_phase):
        phase_id = due_phase.id
        Phase.objects.filter(pk=phase_id).delete()

        assert _claim(phase_id) == 0

    @pytest.mark.django_db
    def test_a_game_paused_after_arming_is_not_resolved_when_the_job_runs(self, due_phase):
        due_phase.game.pause()

        with patch.object(Phase.objects, "_resolve_claimed") as mock_resolve:
            assert Phase.objects.resolve_if_due(due_phase.id) is None

        mock_resolve.assert_not_called()
        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.ACTIVE


class TestLockIfActive:

    @pytest.mark.django_db
    def test_returns_the_phase_and_locks_the_row(self, order_active_game):
        phase = order_active_game.current_phase

        with transaction.atomic():
            with CaptureQueriesContext(connection) as queries:
                locked = Phase.objects.lock_if_active(phase.id)

        assert locked == phase
        assert "FOR UPDATE" in queries[0]["sql"]

    @pytest.mark.django_db
    def test_returns_none_while_the_phase_is_processing(self, order_active_game):
        phase = order_active_game.current_phase
        Phase.objects.filter(pk=phase.pk).update(status=PhaseStatus.PROCESSING)

        with transaction.atomic():
            assert Phase.objects.lock_if_active(phase.id) is None


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


class TestDeadlineGridPreservation:

    @pytest.mark.django_db
    def test_next_deadline_anchored_to_scheduled_resolution_not_now(
        self, classical_variant
    ):
        phase1_scheduled = datetime(2026, 1, 3, 21, 0, 0, tzinfo=dt_timezone.utc)

        game = Game.objects.create(
            variant=classical_variant,
            name="Grid Test",
            status="active",
            deadline_mode=DeadlineMode.FIXED_TIME,
            movement_frequency=PhaseFrequency.DAILY,
            fixed_deadline_time=time(21, 0),
            fixed_deadline_timezone="UTC",
        )

        next_with_reference = game.get_scheduled_resolution(
            "Movement", reference_time=phase1_scheduled
        )
        next_from_now = game.get_scheduled_resolution("Movement")

        expected = datetime(2026, 1, 4, 21, 0, 0, tzinfo=dt_timezone.utc)
        assert next_with_reference == expected
        assert next_from_now != expected

    @pytest.mark.django_db
    def test_drifted_early_resolution_compresses_next_deadline_into_range(
        self, italy_vs_germany_phase_with_orders, mock_adjudication_data_basic
    ):
        phase = italy_vs_germany_phase_with_orders
        game = phase.game
        game.deadline_mode = DeadlineMode.FIXED_TIME
        game.movement_frequency = PhaseFrequency.DAILY
        game.fixed_deadline_time = time(12, 0)
        game.fixed_deadline_timezone = "UTC"
        game.save()

        now = timezone.now()
        grid_slot = now.replace(hour=12, minute=0, second=0, microsecond=0)
        if grid_slot <= now:
            grid_slot += timedelta(days=1)
        far_slot = grid_slot + timedelta(days=4)
        phase.scheduled_resolution = far_slot
        phase.save()

        uncompressed = game.get_scheduled_resolution("Retreat", reference_time=far_slot)
        assert uncompressed - timezone.now() > timedelta(hours=48)

        new_phase = Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        run = new_phase.scheduled_resolution - timezone.now()
        assert timedelta(hours=24) <= run < timedelta(hours=48)
        assert new_phase.scheduled_resolution < uncompressed
        assert new_phase.scheduled_resolution.astimezone(dt_timezone.utc).hour == 12
        assert new_phase.scheduled_resolution.minute == 0

    @pytest.mark.django_db
    def test_on_grid_resolution_leaves_next_deadline_uncompressed(
        self, italy_vs_germany_phase_with_orders, mock_adjudication_data_basic
    ):
        phase = italy_vs_germany_phase_with_orders
        game = phase.game
        game.deadline_mode = DeadlineMode.FIXED_TIME
        game.movement_frequency = PhaseFrequency.DAILY
        game.fixed_deadline_time = time(12, 0)
        game.fixed_deadline_timezone = "UTC"
        game.save()

        now = timezone.now()
        near_slot = now.replace(hour=12, minute=0, second=0, microsecond=0)
        if near_slot <= now:
            near_slot += timedelta(days=1)
        phase.scheduled_resolution = near_slot
        phase.save()

        uncompressed = game.get_scheduled_resolution("Retreat", reference_time=near_slot)

        new_phase = Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        run = new_phase.scheduled_resolution - timezone.now()
        assert timedelta(hours=24) <= run < timedelta(hours=48)
        assert new_phase.scheduled_resolution == uncompressed

    @pytest.mark.django_db
    def test_duration_game_deadline_is_not_compressed(
        self, italy_vs_germany_phase_with_orders, mock_adjudication_data_basic
    ):
        phase = italy_vs_germany_phase_with_orders
        assert phase.game.deadline_mode == DeadlineMode.DURATION

        new_phase = Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        run = new_phase.scheduled_resolution - timezone.now()
        expected = phase.game.movement_phase_duration_seconds
        assert abs(run.total_seconds() - expected) < 2


class TestResolutionJobFetchability:

    @pytest.mark.django_db
    def test_a_deadline_job_blocks_a_later_job_holding_the_same_lock(self):
        lock = ResolutionJob.lock_for_game("head-of-line")
        blocker = procrastinate_app.configure_task(
            ResolutionJob.TASK_NAME,
            schedule_at=timezone.now() + timedelta(hours=24),
            lock=lock,
        ).defer(phase_id=1)
        follower = procrastinate_app.configure_task(
            ResolutionJob.TASK_NAME,
            lock=lock,
        ).defer(phase_id=1)

        assert blocker < follower
        assert _fetchable_job_ids() == []

        procrastinate_app.job_manager.cancel_job_by_id(blocker)

        assert _fetchable_job_ids() == [follower]

    @pytest.mark.django_db
    def test_the_job_pulled_forward_by_a_confirm_is_fetchable(
        self, phase_factory, classical_england_nation
    ):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.refresh_from_db()
        deadline_job_id = phase.resolution_job_id
        assert _fetchable_job_ids() == []

        PhaseStateSerializer().update(phase.phase_states.first(), {})

        phase.refresh_from_db()
        assert phase.resolution_job_id != deadline_job_id
        assert phase.resolution_job_id in _fetchable_job_ids()


class TestPhaseCreationArming:

    @pytest.mark.django_db
    def test_a_phase_born_all_confirmed_is_armed_immediately(
        self, italy_vs_germany_phase_with_orders, mock_adjudication_data_basic
    ):
        previous_phase = italy_vs_germany_phase_with_orders
        previous_phase.game.members.update(civil_disorder=True)

        new_phase = Phase.objects.create_from_adjudication_data(
            Phase.objects.with_related_data().get(pk=previous_phase.pk),
            mock_adjudication_data_basic,
        )

        assert new_phase.phase_states.filter(orders_confirmed=False, has_possible_orders=True).count() == 0
        job = _armed_job(new_phase)
        assert job is not None
        assert job.scheduled_at is None

    @pytest.mark.django_db
    def test_a_phase_born_with_no_actionable_states_is_armed_immediately(
        self, italy_vs_germany_phase_with_orders, mock_adjudication_data_basic
    ):
        previous_phase = italy_vs_germany_phase_with_orders

        new_phase = Phase.objects.create_from_adjudication_data(
            Phase.objects.with_related_data().get(pk=previous_phase.pk),
            mock_adjudication_data_basic,
        )

        assert new_phase.scheduled_resolution is not None
        assert new_phase.phase_states.filter(has_possible_orders=True).count() == 0
        job = _armed_job(new_phase)
        assert job is not None
        assert job.scheduled_at is None


class TestNoOpRearming:

    @pytest.fixture
    def due_phase(self, phase_factory, classical_england_nation):
        return phase_factory(
            scheduled_resolution=timezone.now() - timedelta(hours=1),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

    @pytest.mark.django_db
    def test_an_nmr_extension_rearms_at_the_new_deadline(self, due_phase):
        due_phase.game.members.update(nmr_extensions_remaining=1)
        due_phase.refresh_from_db()
        original_job_id = due_phase.resolution_job_id

        Phase.objects.resolve_if_due(due_phase.id)

        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.ACTIVE
        assert due_phase.processing_started_at is None
        assert due_phase.scheduled_resolution > timezone.now()
        assert due_phase.resolution_job_id != original_job_id
        assert _armed_job(due_phase).scheduled_at == due_phase.scheduled_resolution
        assert len(_todo_resolve_jobs()) == 1

    @pytest.mark.django_db
    def test_a_claim_lost_to_another_worker_does_not_rearm(self, due_phase):
        due_phase.refresh_from_db()
        original_job_id = due_phase.resolution_job_id
        Phase.objects.filter(pk=due_phase.pk).update(status=PhaseStatus.PROCESSING)

        assert Phase.objects.resolve_if_due(due_phase.id) is None

        due_phase.refresh_from_db()
        assert due_phase.resolution_job_id == original_job_id

    @pytest.mark.django_db
    def test_a_failed_resolution_does_not_arm_a_second_job(self, due_phase):
        due_phase.refresh_from_db()
        original_job_id = due_phase.resolution_job_id

        with patch.object(Phase.objects, "_set_orders_outcome", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                resolve_phase.func(phase_id=due_phase.id)

        due_phase.refresh_from_db()
        assert due_phase.status == PhaseStatus.ACTIVE
        assert due_phase.processing_started_at is None
        assert due_phase.resolution_job_id == original_job_id
        assert len(_todo_resolve_jobs()) == 1


class TestPauseAndUnpause:

    @pytest.fixture
    def armed_phase(self, phase_factory, classical_england_nation):
        return phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

    @pytest.mark.django_db
    def test_pausing_cancels_the_armed_job(self, armed_phase):
        armed_phase.refresh_from_db()
        job_id = armed_phase.resolution_job_id

        armed_phase.game.pause()

        armed_phase.refresh_from_db()
        assert armed_phase.resolution_job_id is None
        cancelled = procrastinate_app.job_manager.list_jobs(id=job_id)[0]
        assert cancelled.status == ResolutionJob.CANCELLED

    @pytest.mark.django_db
    def test_unpausing_rearms_at_the_extended_deadline(self, armed_phase):
        game = armed_phase.game
        game.pause()
        game.unpause()

        armed_phase.refresh_from_db()
        assert armed_phase.resolution_job_id is not None
        assert _armed_job(armed_phase).scheduled_at == armed_phase.scheduled_resolution


class TestMembershipChangeArming:

    @pytest.mark.django_db
    def test_civil_disorder_recovery_pushes_the_job_back_to_the_deadline(
        self, phase_factory, classical_england_nation
    ):
        deadline = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=deadline,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
            ],
        )
        phase.game.members.update(civil_disorder=True)
        Phase.objects.arm_resolution(phase)
        assert _armed_job(phase).scheduled_at is None

        member = phase.game.members.first()
        member.civil_disorder = False
        member.save(update_fields=["civil_disorder"])
        phase.phase_states.filter(member=member).update(orders_confirmed=False)
        Phase.objects.arm_resolution(phase)

        assert _armed_job(phase).scheduled_at == deadline

    @pytest.mark.django_db
    def test_removing_the_last_unconfirmed_member_pulls_the_job_forward(
        self, phase_factory, classical_england_nation, classical_france_nation, secondary_user
    ):
        deadline = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=deadline,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
                {
                    "nation": classical_france_nation,
                    "user": secondary_user,
                    "has_possible_orders": True,
                    "orders_confirmed": False,
                },
            ],
        )
        assert _armed_job(phase).scheduled_at == deadline

        Member.objects.remove(phase.game.members.get(nation=classical_france_nation))

        assert _armed_job(phase).scheduled_at is None

    @pytest.mark.django_db
    def test_handing_over_a_seat_pushes_the_job_back_to_the_deadline(
        self, phase_factory, classical_england_nation, secondary_user
    ):
        deadline = timezone.now() + timedelta(hours=24)
        phase = phase_factory(
            scheduled_resolution=deadline,
            options={"England": {"lon": {"Next": {"Hold": {}}, "Type": "Province"}}},
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
            ],
        )
        Phase.objects.arm_resolution(phase)
        assert _armed_job(phase).scheduled_at is None

        Member.objects.hand_over_seat(
            phase.game.members.get(nation=classical_england_nation), secondary_user
        )

        assert _armed_job(phase).scheduled_at == deadline


class TestResolutionJobBackfill:

    @pytest.mark.django_db
    def test_arms_a_live_phase_that_has_no_job(self, phase_factory, classical_england_nation):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.refresh_from_db()
        procrastinate_app.job_manager.cancel_job_by_id(phase.resolution_job_id)
        Phase.objects.filter(pk=phase.pk).update(resolution_job_id=None)

        assert Phase.objects.backfill_resolution_jobs() == 1

        phase.refresh_from_db()
        assert phase.resolution_job_id is not None

    @pytest.mark.django_db
    def test_leaves_a_correctly_armed_phase_alone(self, phase_factory, classical_england_nation):
        phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        assert Phase.objects.backfill_resolution_jobs() == 0

    @pytest.mark.django_db
    def test_pulls_forward_a_phase_that_is_already_resolvable(
        self, phase_factory, classical_england_nation
    ):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
            ],
        )

        assert Phase.objects.backfill_resolution_jobs() == 1

        assert _armed_job(phase).scheduled_at is None

    @pytest.mark.django_db
    def test_skips_a_paused_game(self, phase_factory, classical_england_nation):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.game.pause()

        assert Phase.objects.backfill_resolution_jobs() == 0

        phase.refresh_from_db()
        assert phase.resolution_job_id is None
