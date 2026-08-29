import pytest
from django.urls import reverse
from rest_framework import status

from common.constants import DeadlineMode, MovementPhaseDuration
from game.models import Game


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
