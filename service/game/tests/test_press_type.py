import pytest
from django.urls import reverse
from rest_framework import status
from common.constants import GameStatus, PressType
from game.models import Game


retrieve_viewname = "game-retrieve"
list_viewname = "game-list"
create_viewname = "game-create"


class TestPressTypeCreate:

    @pytest.mark.django_db
    def test_create_game_with_no_press_persists_value(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "No Press Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": "random",
            "private": False,
            "deadline_mode": "duration",
            "press_type": PressType.NO_PRESS,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["press_type"] == PressType.NO_PRESS

        game = Game.objects.get(id=response.data["id"])
        assert game.press_type == PressType.NO_PRESS

    @pytest.mark.django_db
    def test_create_game_defaults_to_full_press(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Default Press Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": "random",
            "private": False,
            "deadline_mode": "duration",
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["press_type"] == PressType.FULL_PRESS

    @pytest.mark.django_db
    def test_create_game_with_full_press_persists_value(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Full Press Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": "random",
            "private": False,
            "deadline_mode": "duration",
            "press_type": PressType.FULL_PRESS,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["press_type"] == PressType.FULL_PRESS


class TestPressTypeRetrieve:

    @pytest.mark.django_db
    def test_retrieve_game_returns_press_type(
        self, authenticated_client, db, classical_variant, primary_user, base_pending_phase
    ):
        game = Game.objects.create(
            name="Press Retrieve Test Game",
            variant=classical_variant,
            status=GameStatus.PENDING,
            press_type=PressType.NO_PRESS,
        )
        base_pending_phase(game)
        game.members.create(user=primary_user, is_game_master=True)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["press_type"] == PressType.NO_PRESS

    @pytest.mark.django_db
    def test_retrieve_game_returns_full_press_by_default(
        self, authenticated_client, pending_game_created_by_primary_user
    ):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["press_type"] == PressType.FULL_PRESS


class TestPressTypeList:

    @pytest.mark.django_db
    def test_list_games_returns_press_type(
        self, authenticated_client, db, classical_variant, primary_user, base_pending_phase
    ):
        game = Game.objects.create(
            name="Press List Test Game",
            variant=classical_variant,
            status=GameStatus.PENDING,
            press_type=PressType.NO_PRESS,
        )
        base_pending_phase(game)
        game.members.create(user=primary_user, is_game_master=True)

        url = reverse(list_viewname)
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        game_data = next(g for g in results if g["id"] == game.id)
        assert game_data["press_type"] == PressType.NO_PRESS
