import pytest
from django.urls import reverse
from rest_framework import status

from game.models import Game

create_viewname = "game-create"
leave_viewname = "game-leave"


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
    def test_can_manage_true_for_creator_after_leaving_game(
        self, api_client, pending_game_factory, secondary_user
    ):
        game = pending_game_factory()
        creator = game.created_by
        game.members.create(user=secondary_user)

        api_client.force_authenticate(user=creator)
        response = api_client.delete(reverse(leave_viewname, args=[game.id]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

        game.refresh_from_db()
        assert not game.members.filter(user=creator).exists()
        assert game.can_manage(creator) is True
