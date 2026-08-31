from datetime import time, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from procrastinate.contrib.django import app as procrastinate_app
from rest_framework import status

from common.constants import (
    DeadlineMode,
    GameStatus,
    MovementPhaseDuration,
    MusterJob,
    PhaseFrequency,
    PhaseStatus,
)
from game.models import Game
from notification.models import Notification
from phase.models import Phase


def _job(job_id):
    if job_id is None:
        return None
    jobs = procrastinate_app.job_manager.list_jobs(id=job_id)
    return jobs[0] if jobs else None


def _expiry_job(game):
    game.refresh_from_db()
    return _job(game.muster_job_id)


@pytest.fixture
def muster_game_factory(db, primary_user, secondary_user, italy_vs_germany_variant):
    def _create(muster_required=True, private=True, fill=True, second_user=None, **kwargs):
        kwargs.setdefault("deadline_mode", DeadlineMode.DURATION)
        kwargs.setdefault("movement_phase_duration", MovementPhaseDuration.TWENTY_FOUR_HOURS)
        game = Game.objects.create_from_template(
            italy_vs_germany_variant,
            name="Muster Game",
            created_by=primary_user,
            admin=primary_user,
            private=private,
            muster_required=muster_required,
            **kwargs,
        )
        game.channels.create(name="Public Press", private=False)
        game.seat(primary_user)
        game.seat(second_user or secondary_user)
        if fill:
            game.start_if_full()
            game.refresh_from_db()
        return game

    return _create


class TestFillTransition:

    @pytest.mark.django_db
    def test_full_game_with_muster_required_enters_mustering(
        self, muster_game_factory, in_memory_procrastinate
    ):
        before = timezone.now()
        game = muster_game_factory()

        assert game.status == GameStatus.MUSTERING
        assert game.muster_deadline is not None
        expected = before + timedelta(hours=24)
        assert abs((game.muster_deadline - expected).total_seconds()) < 60
        assert all(m.nation_id is None for m in game.members.all())
        assert game.current_phase.status == PhaseStatus.PENDING

    @pytest.mark.django_db
    def test_full_game_without_muster_required_starts(
        self, muster_game_factory, in_memory_procrastinate
    ):
        game = muster_game_factory(muster_required=False)

        assert game.status == GameStatus.ACTIVE
        assert game.muster_deadline is None
        assert game.current_phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_null_effective_duration_starts_immediately(
        self, muster_game_factory, in_memory_procrastinate
    ):
        game = muster_game_factory(
            deadline_mode=DeadlineMode.FIXED_TIME,
            movement_phase_duration=None,
            movement_frequency=None,
        )

        assert game.status == GameStatus.ACTIVE
        assert game.muster_deadline is None

    @pytest.mark.django_db
    def test_mustering_started_notifies_members(
        self, muster_game_factory, in_memory_procrastinate, primary_user, secondary_user
    ):
        muster_game_factory()

        recipients = set(
            Notification.objects.filter(event_type="mustering_started").values_list(
                "recipient_id", flat=True
            )
        )
        assert recipients == {primary_user.id, secondary_user.id}


class TestMusterDeadline:

    @pytest.mark.django_db
    def test_duration_mode_uses_movement_phase_duration(
        self, muster_game_factory, in_memory_procrastinate
    ):
        game = muster_game_factory(
            movement_phase_duration=MovementPhaseDuration.TWELVE_HOURS
        )

        expected = timezone.now() + timedelta(hours=12)
        assert abs((game.muster_deadline - expected).total_seconds()) < 60

    @pytest.mark.django_db
    def test_fixed_time_mode_uses_frequency_interval(
        self, muster_game_factory, in_memory_procrastinate
    ):
        game = muster_game_factory(
            deadline_mode=DeadlineMode.FIXED_TIME,
            movement_phase_duration=None,
            movement_frequency=PhaseFrequency.DAILY,
            fixed_deadline_time=time(hour=23, minute=59),
            fixed_deadline_timezone="UTC",
        )

        expected = timezone.now() + timedelta(days=1)
        assert abs((game.muster_deadline - expected).total_seconds()) < 60


class TestArming:

    @pytest.mark.django_db
    def test_entering_mustering_arms_expiry_at_deadline(
        self, muster_game_factory, in_memory_procrastinate
    ):
        game = muster_game_factory()

        job = _expiry_job(game)
        assert job is not None
        assert job.status == MusterJob.TODO
        assert job.scheduled_at == game.muster_deadline

    @pytest.mark.django_db
    def test_partial_confirmation_keeps_deadline_schedule(
        self, muster_game_factory, in_memory_procrastinate, authenticated_client
    ):
        game = muster_game_factory()
        job_id_before = game.muster_job_id

        response = authenticated_client.post(reverse("game-muster", args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        job = _expiry_job(game)
        assert game.muster_job_id == job_id_before
        assert job.scheduled_at == game.muster_deadline

    @pytest.mark.django_db
    def test_final_confirmation_arms_immediately(
        self,
        muster_game_factory,
        in_memory_procrastinate,
        authenticated_client,
        authenticated_client_for_secondary_user,
    ):
        game = muster_game_factory()

        authenticated_client.post(reverse("game-muster", args=[game.id]))
        response = authenticated_client_for_secondary_user.post(
            reverse("game-muster", args=[game.id])
        )

        assert response.status_code == status.HTTP_200_OK
        job = _expiry_job(game)
        assert job.status == MusterJob.TODO
        assert job.scheduled_at is None

    @pytest.mark.django_db
    def test_bots_do_not_block_the_final_confirmation(
        self, muster_game_factory, in_memory_procrastinate, authenticated_client, bot_user
    ):
        game = muster_game_factory(second_user=bot_user)

        response = authenticated_client.post(reverse("game-muster", args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        assert _expiry_job(game).scheduled_at is None


class TestStartIfMustered:

    @pytest.mark.django_db
    def test_expiry_starts_game_and_vacates_unconfirmed_seats(
        self,
        muster_game_factory,
        in_memory_procrastinate,
        authenticated_client,
        primary_user,
        secondary_user,
    ):
        game = muster_game_factory()
        authenticated_client.post(reverse("game-muster", args=[game.id]))

        Game.objects.start_if_mustered(game.id)

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE
        assert game.muster_deadline is None

        confirmed = game.members.get(user=primary_user)
        removed = game.members.get(user=secondary_user)
        assert confirmed.kicked is False
        assert removed.kicked is True
        assert removed.nation_id is not None
        assert removed.replaceable is True

        phase = game.current_phase
        assert phase.status == PhaseStatus.ACTIVE
        removed_state = phase.phase_states.get(member=removed)
        assert removed_state.has_possible_orders is False

    @pytest.mark.django_db
    def test_expiry_with_all_confirmed_removes_nobody(
        self,
        muster_game_factory,
        in_memory_procrastinate,
        authenticated_client,
        authenticated_client_for_secondary_user,
    ):
        game = muster_game_factory()
        authenticated_client.post(reverse("game-muster", args=[game.id]))
        authenticated_client_for_secondary_user.post(
            reverse("game-muster", args=[game.id])
        )

        Game.objects.start_if_mustered(game.id)

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE
        assert not game.members.filter(kicked=True).exists()

    @pytest.mark.django_db
    def test_expiry_notifications_split_by_confirmation(
        self,
        muster_game_factory,
        in_memory_procrastinate,
        authenticated_client,
        primary_user,
        secondary_user,
    ):
        game = muster_game_factory()
        authenticated_client.post(reverse("game-muster", args=[game.id]))

        Game.objects.start_if_mustered(game.id)

        start_recipients = set(
            Notification.objects.filter(event_type="game_start").values_list(
                "recipient_id", flat=True
            )
        )
        removed_recipients = set(
            Notification.objects.filter(event_type="removed_from_muster").values_list(
                "recipient_id", flat=True
            )
        )
        assert start_recipients == {primary_user.id}
        assert removed_recipients == {secondary_user.id}

    @pytest.mark.django_db
    def test_vacated_seat_can_be_taken_over(
        self,
        muster_game_factory,
        in_memory_procrastinate,
        authenticated_client,
        authenticated_client_for_tertiary_user,
        secondary_user,
    ):
        game = muster_game_factory()
        authenticated_client.post(reverse("game-muster", args=[game.id]))
        Game.objects.start_if_mustered(game.id)

        removed = game.members.get(user=secondary_user)
        response = authenticated_client_for_tertiary_user.post(
            reverse("game-member-replace", args=[game.id, removed.id])
        )

        assert response.status_code == status.HTTP_201_CREATED
        removed.refresh_from_db()
        assert removed.replaced_by_id is not None

    @pytest.mark.django_db
    def test_expiry_keeps_unconfirmed_bots(
        self, muster_game_factory, in_memory_procrastinate, bot_user
    ):
        game = muster_game_factory(second_user=bot_user)

        Game.objects.start_if_mustered(game.id)

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE
        assert game.members.get(user=bot_user).kicked is False

    @pytest.mark.django_db
    def test_start_if_mustered_is_a_noop_for_non_mustering_games(
        self, muster_game_factory, in_memory_procrastinate
    ):
        game = muster_game_factory(muster_required=False)

        assert Game.objects.start_if_mustered(game.id) is None


class TestMusterEndpoint:

    @pytest.mark.django_db
    def test_confirming_sets_mustered_at(
        self, muster_game_factory, in_memory_procrastinate, authenticated_client, primary_user
    ):
        game = muster_game_factory()

        response = authenticated_client.post(reverse("game-muster", args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        member = game.members.get(user=primary_user)
        assert member.mustered_at is not None

    @pytest.mark.django_db
    def test_confirming_twice_is_rejected(
        self, muster_game_factory, in_memory_procrastinate, authenticated_client, primary_user
    ):
        game = muster_game_factory()

        authenticated_client.post(reverse("game-muster", args=[game.id]))
        first = game.members.get(user=primary_user).mustered_at
        response = authenticated_client.post(reverse("game-muster", args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert game.members.get(user=primary_user).mustered_at == first

    @pytest.mark.django_db
    def test_confirming_requires_a_mustering_game(
        self, muster_game_factory, in_memory_procrastinate, authenticated_client
    ):
        game = muster_game_factory(fill=False)

        response = authenticated_client.post(reverse("game-muster", args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_confirming_requires_membership(
        self, muster_game_factory, in_memory_procrastinate, authenticated_client_for_tertiary_user
    ):
        game = muster_game_factory()

        response = authenticated_client_for_tertiary_user.post(
            reverse("game-muster", args=[game.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRosterChange:

    @pytest.mark.django_db
    def test_leaving_returns_the_game_to_pending(
        self,
        muster_game_factory,
        in_memory_procrastinate,
        authenticated_client,
        authenticated_client_for_secondary_user,
    ):
        game = muster_game_factory()
        authenticated_client.post(reverse("game-muster", args=[game.id]))
        expiry_id = game.muster_job_id

        response = authenticated_client_for_secondary_user.delete(
            reverse("game-leave", args=[game.id])
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        game.refresh_from_db()
        assert game.status == GameStatus.PENDING
        assert game.muster_deadline is None
        assert game.muster_job_id is None
        assert _job(expiry_id).status == MusterJob.CANCELLED

    @pytest.mark.django_db
    def test_kick_during_mustering_returns_the_game_to_pending(
        self, muster_game_factory, in_memory_procrastinate, authenticated_client, secondary_user
    ):
        game = muster_game_factory()
        member = game.members.get(user=secondary_user)

        response = authenticated_client.delete(
            reverse("game-kick", args=[game.id, member.id])
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        game.refresh_from_db()
        assert game.status == GameStatus.PENDING
        assert game.muster_deadline is None
        assert not game.members.filter(user=secondary_user).exists()
        assert Notification.objects.filter(
            event_type="kicked_from_staging", recipient=secondary_user
        ).exists()

    @pytest.mark.django_db
    def test_confirmations_survive_a_roster_change(
        self,
        muster_game_factory,
        in_memory_procrastinate,
        authenticated_client,
        authenticated_client_for_secondary_user,
        primary_user,
        tertiary_user,
    ):
        game = muster_game_factory()
        authenticated_client.post(reverse("game-muster", args=[game.id]))

        authenticated_client_for_secondary_user.delete(
            reverse("game-leave", args=[game.id])
        )
        game.refresh_from_db()
        first_deadline_cleared = game.muster_deadline is None

        game.seat(tertiary_user)
        game.start_if_full()

        game.refresh_from_db()
        assert first_deadline_cleared
        assert game.status == GameStatus.MUSTERING
        assert game.muster_deadline is not None
        assert game.members.get(user=primary_user).mustered_at is not None
        assert game.members.get(user=tertiary_user).mustered_at is None


class TestStatusAudit:

    @pytest.mark.django_db
    def test_cannot_join_a_mustering_game(
        self, muster_game_factory, in_memory_procrastinate, authenticated_client_for_tertiary_user
    ):
        game = muster_game_factory(private=False)

        response = authenticated_client_for_tertiary_user.post(
            reverse("game-join", args=[game.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_game_master_can_delete_a_mustering_game(
        self,
        db,
        primary_user,
        secondary_user,
        tertiary_user,
        italy_vs_germany_variant,
        in_memory_procrastinate,
        authenticated_client,
    ):
        game = Game.objects.create_from_template(
            italy_vs_germany_variant,
            name="GM Muster Game",
            created_by=primary_user,
            game_master=primary_user,
            admin=primary_user,
            private=True,
            muster_required=True,
            deadline_mode=DeadlineMode.DURATION,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        game.channels.create(name="Public Press", private=False)
        game.seat(secondary_user)
        game.seat(tertiary_user)
        game.start_if_full()
        game.refresh_from_db()
        assert game.status == GameStatus.MUSTERING

        response = authenticated_client.delete(reverse("game-delete", args=[game.id]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Game.objects.filter(id=game.id).exists()

    @pytest.mark.django_db
    def test_account_deletion_returns_mustering_games_to_pending(
        self,
        db,
        primary_user,
        user_factory,
        authenticated_client_factory,
        italy_vs_germany_variant,
        in_memory_procrastinate,
    ):
        deleted_user = user_factory()
        game = Game.objects.create_from_template(
            italy_vs_germany_variant,
            name="Account Deletion Muster Game",
            created_by=primary_user,
            admin=primary_user,
            private=True,
            muster_required=True,
            deadline_mode=DeadlineMode.DURATION,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        game.channels.create(name="Public Press", private=False)
        game.seat(primary_user)
        game.seat(deleted_user)
        game.start_if_full()
        game.refresh_from_db()
        assert game.status == GameStatus.MUSTERING

        response = authenticated_client_factory(deleted_user).delete(
            reverse("user-delete")
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        game.refresh_from_db()
        assert game.status == GameStatus.PENDING
        assert game.muster_deadline is None
        assert game.members.count() == 1

    @pytest.mark.django_db
    def test_civil_disorder_removal_returns_mustering_games_to_pending(
        self, muster_game_factory, in_memory_procrastinate, secondary_user
    ):
        game = muster_game_factory()

        Phase.objects._remove_from_staging_games([secondary_user.id])

        game.refresh_from_db()
        assert game.status == GameStatus.PENDING
        assert not game.members.filter(user=secondary_user).exists()


class TestGameCreateMusterRequired:

    def _payload(self, variant_id, **overrides):
        payload = {
            "name": "Create Muster Game",
            "variant_id": variant_id,
            "nation_assignment": "random",
            "private": False,
            "deadline_mode": DeadlineMode.DURATION,
            "movement_phase_duration": MovementPhaseDuration.TWENTY_FOUR_HOURS,
        }
        payload.update(overrides)
        return payload

    @pytest.mark.django_db
    def test_private_games_default_muster_required_off(
        self, authenticated_client, italy_vs_germany_variant, in_memory_procrastinate
    ):
        response = authenticated_client.post(
            reverse("game-create"),
            self._payload(italy_vs_germany_variant.id, private=True),
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Game.objects.get(id=response.data["id"]).muster_required is False

    @pytest.mark.django_db
    def test_private_games_can_opt_into_mustering(
        self, authenticated_client, italy_vs_germany_variant, in_memory_procrastinate
    ):
        response = authenticated_client.post(
            reverse("game-create"),
            self._payload(italy_vs_germany_variant.id, private=True, muster_required=True),
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Game.objects.get(id=response.data["id"]).muster_required is True
