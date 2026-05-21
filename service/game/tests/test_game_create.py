import pytest
from django.urls import reverse
from rest_framework import status

from game.models import Game

create_viewname = "game-create"


def fixed_time_payload(variant_id):
    return {
        "name": "Test Fixed Time Game",
        "variant_id": variant_id,
        "nation_assignment": "random",
        "private": False,
        "deadline_mode": "fixed_time",
        "fixed_deadline_time": "09:00:00",
        "fixed_deadline_timezone": "UTC",
        "movement_frequency": "hourly",
        "movement_phase_duration": "24 hours",
    }


def duration_payload(variant_id):
    return {
        "name": "Test Duration Game",
        "variant_id": variant_id,
        "nation_assignment": "random",
        "private": False,
        "deadline_mode": "duration",
        "movement_phase_duration": "12 hours",
        "movement_frequency": "hourly",
        "fixed_deadline_time": "09:00:00",
        "fixed_deadline_timezone": "UTC",
    }


class TestGameCreateView:

    @pytest.mark.django_db
    def test_fixed_time_game_nulls_movement_phase_duration(
        self, authenticated_client, classical_variant
    ):
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, fixed_time_payload(classical_variant.id), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.movement_phase_duration is None

    @pytest.mark.django_db
    def test_fixed_time_game_nulls_retreat_phase_duration(
        self, authenticated_client, classical_variant
    ):
        payload = {**fixed_time_payload(classical_variant.id), "retreat_phase_duration": "12 hours"}
        url = reverse(create_viewname)
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.retreat_phase_duration is None

    @pytest.mark.django_db
    def test_duration_game_nulls_movement_frequency(
        self, authenticated_client, classical_variant
    ):
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, duration_payload(classical_variant.id), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.movement_frequency is None

    @pytest.mark.django_db
    def test_duration_game_nulls_fixed_deadline_fields(
        self, authenticated_client, classical_variant
    ):
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, duration_payload(classical_variant.id), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.fixed_deadline_time is None
        assert game.fixed_deadline_timezone is None
