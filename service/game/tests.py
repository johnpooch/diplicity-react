import pytest
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from rest_framework import status
from common.constants import PhaseStatus, GameStatus, NationAssignment

from .models import Game

retrieve_viewname = "game-retrieve"
list_viewname = "game-list"
create_viewname = "game-create"


class TestGameRetrieveView:

    @pytest.mark.django_db
    def test_retrieve_game_success(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == pending_game_created_by_primary_user.id
        assert response.data["name"] == pending_game_created_by_primary_user.name
        assert response.data["status"] == pending_game_created_by_primary_user.status
        assert response.data["movement_phase_duration"] == pending_game_created_by_primary_user.movement_phase_duration
        assert response.data["nation_assignment"] == pending_game_created_by_primary_user.nation_assignment
        assert response.data["can_join"] == False
        assert response.data["can_leave"] == True
        assert response.data["phase_confirmed"] == False
        assert response.data["phases"][0]["id"] == pending_game_created_by_primary_user.phases.first().id
        assert response.data["members"][0]["id"] == pending_game_created_by_primary_user.members.first().id
        assert response.data["variant"]["id"] == pending_game_created_by_primary_user.variant.id

    @pytest.mark.django_db
    def test_retrieve_game_unauthenticated(self, unauthenticated_client, pending_game_created_by_primary_user):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_retrieve_game_not_found(self, authenticated_client):
        url = reverse(retrieve_viewname, args=["non-existent-game"])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_retrieve_game_response_structure(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        required_fields = [
            "id",
            "name",
            "status",
            "movement_phase_duration",
            "nation_assignment",
            "can_join",
            "can_leave",
            "phases",
            "members",
            "variant",
            "phase_confirmed",
        ]
        for field in required_fields:
            assert field in response.data

        assert isinstance(response.data["can_join"], bool)
        assert isinstance(response.data["can_leave"], bool)
        assert isinstance(response.data["phase_confirmed"], bool)
        assert isinstance(response.data["phases"], list)
        assert isinstance(response.data["members"], list)
        assert isinstance(response.data["variant"], dict)

    @pytest.mark.django_db
    def test_can_join_true_pending_game_non_member(
        self, authenticated_client_for_secondary_user, pending_game_created_by_primary_user
    ):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client_for_secondary_user.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_join"] is True

    @pytest.mark.django_db
    def test_can_join_false_pending_game_already_member(
        self, authenticated_client, pending_game_created_by_primary_user
    ):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_join"] is False

    @pytest.mark.django_db
    def test_can_join_false_active_game(
        self, authenticated_client_for_secondary_user, active_game_created_by_primary_user
    ):
        url = reverse(retrieve_viewname, args=[active_game_created_by_primary_user.id])
        response = authenticated_client_for_secondary_user.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_join"] is False

    @pytest.mark.django_db
    def test_can_leave_true_pending_game_member(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_leave"] is True

    @pytest.mark.django_db
    def test_can_leave_false_pending_game_non_member(
        self, authenticated_client_for_secondary_user, pending_game_created_by_primary_user
    ):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client_for_secondary_user.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_leave"] is False

    @pytest.mark.django_db
    def test_can_leave_false_active_game(self, authenticated_client, active_game_with_phase_state):
        url = reverse(retrieve_viewname, args=[active_game_with_phase_state.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_leave"] is False

    @pytest.mark.django_db
    def test_phase_confirmed_true(self, authenticated_client, active_game_with_confirmed_phase_state):
        url = reverse(retrieve_viewname, args=[active_game_with_confirmed_phase_state.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["phase_confirmed"] is True

    @pytest.mark.django_db
    def test_phase_confirmed_false(self, authenticated_client, active_game_with_phase_state):
        url = reverse(retrieve_viewname, args=[active_game_with_phase_state.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["phase_confirmed"] is False

    @pytest.mark.django_db
    def test_phase_confirmed_false_other_user(
        self, authenticated_client_for_secondary_user, active_game_with_confirmed_phase_state
    ):
        url = reverse(retrieve_viewname, args=[active_game_with_confirmed_phase_state.id])
        response = authenticated_client_for_secondary_user.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["phase_confirmed"] is False

    @pytest.mark.django_db
    def test_phase_confirmed_false_no_phases(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["phase_confirmed"] is False

    @pytest.mark.django_db
    def test_game_with_multiple_members(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        secondary_user,
        classical_england_nation,
        classical_france_nation,
    ):
        game = Game.objects.create(
            name="Multi-Member Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)
        game.members.create(user=secondary_user, nation=classical_france_nation)

        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )

        phase.phase_states.create(member=game.members.first())
        phase.phase_states.create(member=game.members.last())

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert len(response.data["members"]) == 2
        assert response.data["can_join"] is False
        assert response.data["can_leave"] is False

        member_usernames = [member["username"] for member in response.data["members"]]
        assert primary_user.username in member_usernames
        assert secondary_user.username in member_usernames

    @pytest.mark.django_db
    def test_game_with_multiple_phases(
        self, authenticated_client, active_game_with_phase_state, classical_england_nation, classical_edinburgh_province
    ):
        game = active_game_with_phase_state

        second_phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Fall",
            year=1901,
            type="Movement",
            status=PhaseStatus.COMPLETED,
            ordinal=2,
        )
        second_phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
        second_phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert len(response.data["phases"]) == 2
        phase_seasons = [phase["season"] for phase in response.data["phases"]]
        assert "Spring" in phase_seasons
        assert "Fall" in phase_seasons

        for phase in response.data["phases"]:
            assert "units" in phase
            assert "supply_centers" in phase
            assert isinstance(phase["units"], list)
            assert isinstance(phase["supply_centers"], list)


class TestGameRetrieveViewQueryPerformance:

    @pytest.mark.django_db
    def test_retrieve_game_query_count_simple(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)
        assert query_count == 30

    @pytest.mark.django_db
    def test_retrieve_game_query_count_multiple_phases_with_units(
        self,
        authenticated_client,
        active_game_with_phase_state,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
        classical_london_province,
        classical_paris_province,
    ):
        game = active_game_with_phase_state

        for i in range(3):
            phase = game.phases.create(
                game=game,
                variant=game.variant,
                season="Fall",
                year=1901 + i,
                type="Movement",
                status=PhaseStatus.COMPLETED,
                ordinal=2 + i,
            )
            phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
            phase.units.create(type="Army", nation=classical_england_nation, province=classical_london_province)
            phase.units.create(type="Army", nation=classical_france_nation, province=classical_paris_province)

            phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)
            phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
            phase.supply_centers.create(nation=classical_france_nation, province=classical_paris_province)

        url = reverse(retrieve_viewname, args=[game.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)
        assert query_count == 31


class TestGameListView:

    @pytest.mark.django_db
    def test_list_games_success(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(list_viewname)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    @pytest.mark.django_db
    def test_list_games_unauthenticated(self, unauthenticated_client):
        url = reverse(list_viewname)
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_list_games_response_structure(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(list_viewname)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        if len(response.data) > 0:
            game = response.data[0]
            required_fields = [
                "id",
                "name",
                "status",
                "movement_phase_duration",
                "nation_assignment",
                "can_join",
                "can_leave",
                "phases",
                "members",
                "variant",
                "phase_confirmed",
            ]
            for field in required_fields:
                assert field in game

    @pytest.mark.django_db
    def test_list_games_filter_mine_true(
        self, authenticated_client, pending_game_created_by_primary_user, pending_game_created_by_secondary_user
    ):
        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"mine": "true"})
        assert response.status_code == status.HTTP_200_OK

        game_ids = [game["id"] for game in response.data]
        assert pending_game_created_by_primary_user.id in game_ids
        assert pending_game_created_by_secondary_user.id not in game_ids

    @pytest.mark.django_db
    def test_list_games_filter_mine_false(
        self, authenticated_client, pending_game_created_by_primary_user, pending_game_created_by_secondary_user
    ):
        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"mine": "false"})
        assert response.status_code == status.HTTP_200_OK

        game_ids = [game["id"] for game in response.data]
        assert pending_game_created_by_secondary_user.id in game_ids

    @pytest.mark.django_db
    def test_list_games_filter_can_join_true(
        self, authenticated_client, pending_game_created_by_primary_user, pending_game_created_by_secondary_user
    ):
        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"can_join": "true"})
        assert response.status_code == status.HTTP_200_OK

        for game in response.data:
            assert game["can_join"] is True

    @pytest.mark.django_db
    def test_list_games_combined_filters(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"mine": "true", "can_join": "false"})
        assert response.status_code == status.HTTP_200_OK

        for game in response.data:
            assert game["can_join"] is False

        if len(response.data) > 0:
            game_ids = [game["id"] for game in response.data]
            assert pending_game_created_by_primary_user.id in game_ids

    @pytest.mark.django_db
    def test_list_games_empty_filters(self, authenticated_client):
        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"mine": "", "can_join": ""})
        assert response.status_code == status.HTTP_200_OK


class TestGameListViewQueryPerformance:

    @pytest.mark.django_db
    def test_list_games_query_count_simple(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(list_viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)
        assert query_count <= 30

    @pytest.mark.django_db
    def test_list_games_query_count_with_phases_and_units(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        classical_england_nation,
        classical_edinburgh_province,
    ):
        for i in range(3):
            game = Game.objects.create(
                name=f"Game with Phases {i}",
                variant=classical_variant,
                status=GameStatus.ACTIVE,
            )
            game.members.create(user=primary_user, nation=classical_england_nation)

            for j in range(2):
                phase = game.phases.create(
                    game=game,
                    variant=game.variant,
                    season="Spring" if j == 0 else "Fall",
                    year=1901,
                    type="Movement",
                    status=PhaseStatus.ACTIVE if j == 1 else PhaseStatus.COMPLETED,
                    ordinal=j + 1,
                )
                phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
                phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

        url = reverse(list_viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)
        assert query_count <= 33


class TestGameCreateView:

    @pytest.mark.django_db
    def test_create_game_success(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "New Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert response.data["name"] == payload["name"]
        assert response.data["status"] == GameStatus.PENDING

        required_fields = [
            "id",
            "name",
            "status",
            "movement_phase_duration",
            "nation_assignment",
            "can_join",
            "can_leave",
            "phases",
            "members",
            "variant",
            "phase_confirmed",
        ]
        for field in required_fields:
            assert field in response.data

    @pytest.mark.django_db
    def test_create_game_unauthenticated(self, unauthenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "New Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = unauthenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_create_game_with_ordered_nation_assignment(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Ordered Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.ORDERED,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.nation_assignment == NationAssignment.ORDERED

    @pytest.mark.django_db
    def test_create_game_missing_name(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_create_game_missing_variant_id(self, authenticated_client):
        url = reverse(create_viewname)
        payload = {
            "name": "Test Game",
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "variant_id" in response.data

    @pytest.mark.django_db
    def test_create_game_missing_nation_assignment(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Test Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "nation_assignment" in response.data

    @pytest.mark.django_db
    def test_create_game_invalid_variant_id(self, authenticated_client):
        url = reverse(create_viewname)
        payload = {
            "name": "Test Game",
            "variant_id": "non-existent-variant",
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "variant_id" in response.data

    @pytest.mark.django_db
    def test_create_game_invalid_nation_assignment(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": "invalid-assignment",
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_game_empty_name(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_game_creates_membership(self, authenticated_client, classical_variant, primary_user):
        url = reverse(create_viewname)
        payload = {
            "name": "Membership Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.members.filter(user=primary_user).exists()
        assert game.members.count() == 1

    @pytest.mark.django_db
    def test_create_game_creates_public_channel(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Channel Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        channel = game.channels.filter(private=False).first()
        assert channel is not None
        assert channel.name == "Public Press"

    @pytest.mark.django_db
    def test_create_game_creates_template_phase(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Phase Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        phase = game.phases.first()
        assert phase is not None
        assert phase.status == PhaseStatus.PENDING
        assert phase.ordinal == 1
        assert phase.variant == classical_variant

    @pytest.mark.django_db
    def test_create_game_unique_ids(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Unique ID Test",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }

        response1 = authenticated_client.post(url, payload, format="json")
        response2 = authenticated_client.post(url, payload, format="json")

        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED
        assert response1.data["id"] != response2.data["id"]

    @pytest.mark.django_db
    def test_create_game_special_characters_in_name(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Test Game! @#$%^&*()",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == payload["name"]

    @pytest.mark.django_db
    def test_create_game_unicode_name(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Тест Игра 测试游戏 🎮",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == payload["name"]

    @pytest.mark.django_db
    def test_create_multiple_games_isolated_channels(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)

        payload1 = {
            "name": "Game 1",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        payload2 = {
            "name": "Game 2",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }

        response1 = authenticated_client.post(url, payload1, format="json")
        response2 = authenticated_client.post(url, payload2, format="json")

        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED

        game1 = Game.objects.get(id=response1.data["id"])
        game2 = Game.objects.get(id=response2.data["id"])

        channel1 = game1.channels.filter(private=False).first()
        channel2 = game2.channels.filter(private=False).first()

        assert channel1.id != channel2.id
        assert channel1.name == "Public Press"
        assert channel2.name == "Public Press"

    @pytest.mark.django_db
    def test_create_game_can_join_can_leave_values(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Join Leave Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # Since the user created the game, they should be a member
        # can_join should be False (already a member)
        # can_leave should be True (PENDING game + is a member)
        assert response.data["can_join"] is False
        assert response.data["can_leave"] is True
        assert response.data["phase_confirmed"] is False
