import pytest
from django.urls import reverse
from rest_framework import status

from game.models import Game

create_viewname = "game-create"
leave_viewname = "game-leave"


def _admin_reassigned_jobs(connector):
    return [
        j for j in connector.jobs.values()
        if j["task_name"] == "notification.send_notification"
        and j["args"].get("notification_type") == "game_admin_reassigned"
    ]


def game_payload(variant_id, **overrides):
    payload = {
        "name": "Admin Test Game",
        "variant_id": variant_id,
        "nation_assignment": "random",
        "private": False,
        "deadline_mode": "duration",
        "movement_phase_duration": "24 hours",
    }
    payload.update(overrides)
    return payload


class TestGameAdminField:

    @pytest.mark.django_db
    def test_admin_set_to_creator_for_regular_game(self, authenticated_client, primary_user, classical_variant):
        url = reverse(create_viewname)
        response = authenticated_client.post(url, game_payload(classical_variant.id), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.admin == primary_user
        assert game.admin_id == game.created_by_id

    @pytest.mark.django_db
    def test_admin_set_to_game_master_for_gm_game(self, authenticated_client, primary_user, classical_variant):
        url = reverse(create_viewname)
        payload = game_payload(classical_variant.id, private=True, game_master=True)
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.admin == primary_user
        assert game.admin_id == game.game_master_id

    @pytest.mark.django_db
    def test_admin_reassigned_when_current_admin_leaves_game(
        self, api_client, pending_game_factory, secondary_user, in_memory_procrastinate
    ):
        game = pending_game_factory()
        creator = game.created_by
        game.members.create(user=secondary_user)

        api_client.force_authenticate(user=creator)
        response = api_client.delete(reverse(leave_viewname, args=[game.id]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

        game.refresh_from_db()
        assert not game.members.filter(user=creator).exists()
        assert game.admin == secondary_user
        assert game.can_manage(creator) is False
        assert game.can_manage(secondary_user) is True
        assert len(_admin_reassigned_jobs(in_memory_procrastinate)) == 1

    @pytest.mark.django_db
    def test_admin_unchanged_when_leaving_member_is_not_admin(
        self, api_client, pending_game_factory, secondary_user, in_memory_procrastinate
    ):
        game = pending_game_factory()
        creator = game.created_by
        game.members.create(user=secondary_user)

        api_client.force_authenticate(user=secondary_user)
        response = api_client.delete(reverse(leave_viewname, args=[game.id]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

        game.refresh_from_db()
        assert game.admin == creator
        assert _admin_reassigned_jobs(in_memory_procrastinate) == []


class TestReassignAdmin:

    @pytest.mark.django_db
    def test_reassigns_to_random_eligible_member(
        self, pending_game_factory, secondary_user, in_memory_procrastinate
    ):
        game = pending_game_factory()
        game.members.create(user=secondary_user)

        game.reassign_admin()

        game.refresh_from_db()
        assert game.admin == secondary_user
        jobs = _admin_reassigned_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["args"]["user_ids"] == [secondary_user.id]

    @pytest.mark.django_db
    def test_excludes_kicked_and_civil_disorder_members(
        self, pending_game_factory, secondary_user, member_factory
    ):
        game = pending_game_factory()
        member_factory(game=game, user=secondary_user, kicked=True)
        member_factory(game=game, civil_disorder=True)
        eligible_member = member_factory(game=game)

        game.reassign_admin()

        game.refresh_from_db()
        assert game.admin == eligible_member.user

    @pytest.mark.django_db
    def test_does_nothing_when_no_eligible_candidates(
        self, pending_game_factory, in_memory_procrastinate
    ):
        game = pending_game_factory()
        original_admin = game.admin

        game.reassign_admin()

        game.refresh_from_db()
        assert game.admin == original_admin
        assert _admin_reassigned_jobs(in_memory_procrastinate) == []
