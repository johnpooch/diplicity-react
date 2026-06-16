from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status

from adjudication import service as adjudication_service
from common.constants import GameStatus, MovementPhaseDuration, PhaseStatus
from game.models import Game
from user_profile.models import UserProfile

User = get_user_model()

create_viewname = "game-create"
retrieve_viewname = "game-retrieve"
list_viewname = "game-list"
delete_viewname = "game-delete"
pause_viewname = "game-pause"
unpause_viewname = "game-unpause"
extend_deadline_viewname = "game-extend-deadline"
join_viewname = "game-join"
kick_viewname = "game-kick"
phase_state_list_viewname = "phase-state-list"


def game_master_payload(variant_id, **overrides):
    payload = {
        "name": "GM Game",
        "variant_id": variant_id,
        "nation_assignment": "random",
        "private": True,
        "game_master": True,
        "deadline_mode": "duration",
        "movement_phase_duration": "24 hours",
    }
    payload.update(overrides)
    return payload


class TestGameMasterCreate:

    @pytest.mark.django_db
    def test_create_game_with_game_master(self, authenticated_client, primary_user, classical_variant):
        url = reverse(create_viewname)
        response = authenticated_client.post(url, game_master_payload(classical_variant.id), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.game_master == primary_user
        assert game.created_by == primary_user
        assert game.members.count() == 0
        assert game.channels.filter(private=False).count() == 1

    @pytest.mark.django_db
    def test_create_game_with_game_master_response_fields(
        self, authenticated_client, primary_user, classical_variant
    ):
        url = reverse(create_viewname)
        response = authenticated_client.post(url, game_master_payload(classical_variant.id), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["game_master"]["user_id"] == primary_user.id
        assert response.data["game_master"]["name"] == primary_user.profile.name
        assert response.data["can_manage"] is True
        assert response.data["members"] == []

    @pytest.mark.django_db
    def test_create_public_game_with_game_master_fails(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, game_master_payload(classical_variant.id, private=False), format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "game_master" in response.data

    @pytest.mark.django_db
    def test_create_game_without_game_master_flag(self, authenticated_client, primary_user, classical_variant):
        url = reverse(create_viewname)
        payload = game_master_payload(classical_variant.id)
        del payload["game_master"]
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.game_master is None
        assert game.members.count() == 1
        assert response.data["game_master"] is None
        assert response.data["can_manage"] is True


class TestGameMasterJoin:

    @pytest.mark.django_db
    def test_game_master_cannot_join(self, authenticated_client, pending_game_with_game_master_factory):
        game = pending_game_with_game_master_factory()
        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_other_user_can_join(self, authenticated_client_for_secondary_user, pending_game_with_game_master_factory):
        game = pending_game_with_game_master_factory()
        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.post(url)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_can_join_false_for_game_master(self, authenticated_client, pending_game_with_game_master_factory):
        game = pending_game_with_game_master_factory()
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.data["can_join"] is False

    @pytest.mark.django_db
    def test_game_starts_when_all_nations_filled_by_players(
        self, api_client, pending_game_with_game_master_factory, adjudication_data_classical
    ):
        game = pending_game_with_game_master_factory()
        nation_count = game.variant.nations.count()

        for i in range(nation_count - 1):
            user = User.objects.create_user(f"gm_joiner{i}@test.com", password="testpass")
            UserProfile.objects.create(user=user, name=f"GM Joiner {i}")
            game.members.create(user=user)

        last_user = User.objects.create_user("gm_last_joiner@test.com", password="testpass")
        UserProfile.objects.create(user=last_user, name="GM Last Joiner")
        api_client.force_authenticate(user=last_user)

        url = reverse(join_viewname, args=[game.id])
        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE
        assert game.members.count() == nation_count


class TestGameMasterNotAPlayer:

    @pytest.mark.django_db
    def test_game_master_has_no_member_or_phase_state(
        self, active_game_with_game_master_factory, primary_user
    ):
        game = active_game_with_game_master_factory()
        assert not game.members.filter(user=primary_user).exists()
        assert game.members.count() == game.variant.nations.count()
        assert all(m.nation is not None for m in game.members.all())
        assert not game.current_phase.phase_states.filter(member__user=primary_user).exists()


class TestGameMasterInGameAccess:

    @pytest.mark.django_db
    def test_game_master_can_list_phase_states(self, authenticated_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        url = reverse(phase_state_list_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    @pytest.mark.django_db
    def test_non_member_cannot_list_phase_states(
        self, authenticated_client_for_secondary_user, active_game_with_game_master_factory
    ):
        game = active_game_with_game_master_factory()
        url = reverse(phase_state_list_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


class TestGameMasterPowers:

    @pytest.mark.django_db
    def test_game_master_can_pause(self, authenticated_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        url = reverse(pause_viewname, args=[game.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_paused"] is True

    @pytest.mark.django_db
    def test_game_master_can_unpause(self, authenticated_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        game.pause()
        url = reverse(unpause_viewname, args=[game.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_paused"] is False

    @pytest.mark.django_db
    def test_game_master_can_extend_deadline(self, authenticated_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_player_cannot_pause_when_game_master_set(self, api_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        member = game.members.exclude(user=None).first()
        api_client.force_authenticate(user=member.user)
        url = reverse(pause_viewname, args=[game.id])
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_player_cannot_extend_deadline_when_game_master_set(
        self, api_client, active_game_with_game_master_factory
    ):
        game = active_game_with_game_master_factory()
        member = game.members.exclude(user=None).first()
        api_client.force_authenticate(user=member.user)
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = api_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_game_master_can_kick(
        self, authenticated_client, pending_game_with_game_master_factory, secondary_user
    ):
        game = pending_game_with_game_master_factory()
        member = game.members.create(user=secondary_user)
        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not game.members.filter(id=member.id).exists()

    @pytest.mark.django_db
    def test_player_cannot_kick_when_game_master_set(
        self, api_client, pending_game_with_game_master_factory, secondary_user, tertiary_user
    ):
        game = pending_game_with_game_master_factory()
        game.members.create(user=secondary_user)
        member = game.members.create(user=tertiary_user)
        api_client.force_authenticate(user=secondary_user)
        url = reverse(kick_viewname, args=[game.id, member.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_can_manage_false_for_players(self, api_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        member = game.members.exclude(user=None).first()
        api_client.force_authenticate(user=member.user)
        url = reverse(retrieve_viewname, args=[game.id])
        response = api_client.get(url)
        assert response.data["can_manage"] is False

    @pytest.mark.django_db
    def test_can_manage_false_for_anonymous_user(self, unauthenticated_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        url = reverse(retrieve_viewname, args=[game.id])
        response = unauthenticated_client.get(url)
        assert response.data["can_manage"] is False


class TestGameMasterDelete:

    @pytest.mark.django_db
    def test_game_master_can_delete_pending_game(self, authenticated_client, pending_game_with_game_master_factory):
        game = pending_game_with_game_master_factory()
        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Game.objects.filter(id=game.id).exists()

    @pytest.mark.django_db
    def test_game_master_cannot_delete_active_game(self, authenticated_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_member_cannot_delete_pending_game_master_game(
        self, authenticated_client_for_secondary_user, pending_game_with_game_master_factory, secondary_user
    ):
        game = pending_game_with_game_master_factory()
        game.members.create(user=secondary_user)
        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_can_delete_true_for_game_master_on_pending_game(
        self, authenticated_client, pending_game_with_game_master_factory
    ):
        game = pending_game_with_game_master_factory()
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.data["can_delete"] is True

    @pytest.mark.django_db
    def test_delete_pending_game_notifies_members(
        self, authenticated_client, pending_game_with_game_master_factory, secondary_user, in_memory_procrastinate, mock_immediate_on_commit
    ):
        game = pending_game_with_game_master_factory()
        game.members.create(user=secondary_user)
        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        jobs = [
            j for j in in_memory_procrastinate.jobs.values()
            if j["task_name"] == "notification.send_notification"
            and j["args"].get("notification_type") == "game_deleted"
        ]
        assert len(jobs) == 1
        assert set(jobs[0]["args"]["user_ids"]) == {secondary_user.id}

    @pytest.mark.django_db
    def test_sandbox_delete_still_works(self, authenticated_client, sandbox_game_factory):
        game = sandbox_game_factory()
        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Game.objects.filter(id=game.id).exists()

    @pytest.mark.django_db
    def test_non_member_cannot_delete_sandbox_game(
        self, authenticated_client_for_secondary_user, sandbox_game_factory
    ):
        game = sandbox_game_factory()
        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGameMasterListFilter:

    @pytest.mark.django_db
    def test_mine_includes_game_master_games(self, authenticated_client, pending_game_with_game_master_factory):
        game = pending_game_with_game_master_factory()
        url = reverse(list_viewname) + "?mine=true"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        game_ids = [g["id"] for g in response.data["results"]]
        assert game.id in game_ids

    @pytest.mark.django_db
    def test_mine_excludes_other_users_game_master_games(
        self, authenticated_client_for_secondary_user, pending_game_with_game_master_factory
    ):
        game = pending_game_with_game_master_factory()
        url = reverse(list_viewname) + "?mine=true"
        response = authenticated_client_for_secondary_user.get(url)
        assert response.status_code == status.HTTP_200_OK
        game_ids = [g["id"] for g in response.data["results"]]
        assert game.id not in game_ids

    @pytest.mark.django_db
    def test_list_serializes_game_master(self, authenticated_client, primary_user, pending_game_with_game_master_factory):
        game = pending_game_with_game_master_factory()
        url = reverse(list_viewname) + "?mine=true"
        response = authenticated_client.get(url)
        game_data = next(g for g in response.data["results"] if g["id"] == game.id)
        assert game_data["game_master"]["user_id"] == primary_user.id
        assert game_data["can_manage"] is True


class TestGameMasterNotifications:

    @pytest.mark.django_db
    def test_pause_notification_targets_players_and_says_game_master(
        self,
        authenticated_client,
        active_game_with_game_master_factory,
        primary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game = active_game_with_game_master_factory()
        mock_send_notification_to_users.reset_mock()

        url = reverse(pause_viewname, args=[game.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK

        mock_send_notification_to_users.assert_called_once()
        call_kwargs = mock_send_notification_to_users.call_args[1]
        assert "Game paused by the Game Master" in call_kwargs["body"]
        member_user_ids = {m.user_id for m in game.members.all()}
        assert set(call_kwargs["user_ids"]) == member_user_ids
        assert primary_user.id not in call_kwargs["user_ids"]

    @pytest.mark.django_db
    def test_game_start_notification_includes_game_master(
        self, pending_game_with_game_master_factory, primary_user, adjudication_data_classical, in_memory_procrastinate
    ):
        game = pending_game_with_game_master_factory()
        for i in range(game.variant.nations.count()):
            user = User.objects.create_user(f"gm_start_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=user, name=f"GM Start Player {i}")
            game.members.create(user=user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        jobs = [
            j for j in in_memory_procrastinate.jobs.values()
            if j["task_name"] == "notification.send_notification"
            and j["args"].get("notification_type") == "game_start"
        ]
        assert len(jobs) == 1
        assert primary_user.id in jobs[0]["args"]["user_ids"]

    @pytest.mark.django_db
    def test_phase_resolved_notification_includes_game_master(
        self,
        active_game_with_game_master_factory,
        primary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
        in_memory_procrastinate,
    ):
        game = active_game_with_game_master_factory()
        mock_send_notification_to_users.reset_mock()

        phase = game.current_phase
        phase.status = PhaseStatus.COMPLETED
        phase.save()

        phase_resolved_calls = [
            c for c in mock_send_notification_to_users.call_args_list
            if c[1].get("notification_type") == "phase_resolved"
        ]
        assert len(phase_resolved_calls) == 1
        assert primary_user.id in phase_resolved_calls[0][1]["user_ids"]


class TestGameMasterQueryCounts:

    @pytest.mark.django_db
    def test_retrieve_query_count_unchanged_by_game_master(
        self, authenticated_client, pending_game_factory, pending_game_with_game_master_factory
    ):
        game_without = pending_game_factory()
        game_with = pending_game_with_game_master_factory()

        url_without = reverse(retrieve_viewname, args=[game_without.id])
        url_with = reverse(retrieve_viewname, args=[game_with.id])

        authenticated_client.get(url_without)
        authenticated_client.get(url_with)

        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            authenticated_client.get(url_without)
        count_without = len(connection.queries)

        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            authenticated_client.get(url_with)
        count_with = len(connection.queries)

        assert count_with == count_without
