import pytest
from adjudication import service as adjudication_service
from unittest.mock import patch
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from django.utils import timezone
from datetime import time, timedelta
from rest_framework import status
from common.constants import PhaseStatus, GameStatus, NationAssignment, MovementPhaseDuration, DeadlineMode, PhaseFrequency

from .models import Game

retrieve_viewname = "game-retrieve"
list_viewname = "game-list"
create_viewname = "game-create"
sandbox_create_viewname = "sandbox-game-create"


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
        assert len(response.data["phases"]) == len(pending_game_created_by_primary_user.phases.all())
        assert response.data["members"][0]["id"] == pending_game_created_by_primary_user.members.first().id
        assert response.data["variant_id"] == pending_game_created_by_primary_user.variant.id

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
            "variant_id",
            "phase_confirmed",
        ]
        for field in required_fields:
            assert field in response.data

        assert isinstance(response.data["can_join"], bool)
        assert isinstance(response.data["can_leave"], bool)
        assert isinstance(response.data["phase_confirmed"], bool)
        assert isinstance(response.data["phases"], list)
        assert isinstance(response.data["members"], list)
        assert isinstance(response.data["variant_id"], str)

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

        member_names = [member["name"] for member in response.data["members"]]
        assert primary_user.profile.name in member_names
        assert secondary_user.profile.name in member_names

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


class TestGameRetrieveViewQueryPerformance:

    @pytest.mark.django_db
    def test_retrieve_game_query_count_simple(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)
        assert query_count == 4

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
        assert query_count == 4

    @pytest.mark.django_db
    def test_retrieve_game_query_count_with_multiple_members(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        secondary_user,
        classical_england_nation,
        classical_france_nation,
        classical_germany_nation,
        classical_austria_nation,
        classical_italy_nation,
        classical_russia_nation,
        classical_turkey_nation,
    ):
        from user_profile.models import UserProfile

        users = [primary_user, secondary_user]
        for i in range(5):
            user = type(primary_user).objects.create_user(
                username=f"user{i}",
                email=f"user{i}@test.com",
                password="testpass123"
            )
            UserProfile.objects.create(user=user, name=f"User {i}")
            users.append(user)

        game = Game.objects.create(
            name="Multi-Member Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )

        nations = [
            classical_england_nation,
            classical_france_nation,
            classical_germany_nation,
            classical_austria_nation,
            classical_italy_nation,
            classical_russia_nation,
            classical_turkey_nation,
        ]

        for user, nation in zip(users, nations):
            game.members.create(user=user, nation=nation)

        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )

        # Create phase states for each member
        for member in game.members.all():
            phase.phase_states.create(member=member)

        url = reverse(retrieve_viewname, args=[game.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)

        print(f"\n\n=== TEST: test_retrieve_game_query_count_with_multiple_members ===")
        print(f"Total queries: {query_count}")
        print(f"Number of members: {game.members.count()}")
        print(f"Number of phase_states: {phase.phase_states.count()}")
        for i, query in enumerate(connection.queries, 1):
            sql = query['sql'][:300]
            print(f"{i}. {sql}")

        assert query_count == 4


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
                "variant_id",
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
        assert query_count == 3

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
        for i in range(4):
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

        print("\n" + "=" * 80)
        print(f"QUERY COUNT: {query_count}")
        print("=" * 80)
        for i, query in enumerate(connection.queries, 1):
            print(f"\nQuery {i}:")
            print(f"SQL: {query['sql']}")
            print(f"Time: {query['time']}")
        print("=" * 80 + "\n")

        assert query_count == 3

    @pytest.mark.django_db
    def test_list_games_query_count_with_different_nations(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        classical_england_nation,
        classical_france_nation,
        classical_germany_nation,
        classical_austria_nation,
        classical_edinburgh_province,
    ):
        nations = [
            classical_england_nation,
            classical_france_nation,
            classical_germany_nation,
            classical_austria_nation,
        ]

        for i in range(4):
            game = Game.objects.create(
                name=f"Game {i}",
                variant=classical_variant,
                status=GameStatus.ACTIVE,
            )
            game.members.create(user=primary_user, nation=nations[i])

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
                phase.units.create(type="Fleet", nation=nations[i], province=classical_edinburgh_province)
                phase.supply_centers.create(nation=nations[i], province=classical_edinburgh_province)

        url = reverse(list_viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)

        print("\n" + "=" * 80)
        print(f"QUERY COUNT: {query_count}")
        print("=" * 80)
        for i, query in enumerate(connection.queries, 1):
            print(f"\nQuery {i}:")
            print(f"SQL: {query['sql']}")
            print(f"Time: {query['time']}")
        print("=" * 80 + "\n")

        assert query_count == 3

    @pytest.mark.django_db
    def test_list_games_query_count_with_phase_states(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        secondary_user,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
        classical_germany_nation,
    ):
        for i in range(2):
            game = Game.objects.create(
                name=f"Game {i}",
                variant=classical_variant,
                status=GameStatus.ACTIVE,
            )
            member1 = game.members.create(user=primary_user, nation=classical_england_nation)
            member2 = game.members.create(user=secondary_user, nation=classical_france_nation)
            member3 = game.members.create(user=secondary_user, nation=classical_germany_nation)

            phase = game.phases.create(
                game=game,
                variant=game.variant,
                season="Spring",
                year=1901,
                type="Movement",
                status=PhaseStatus.ACTIVE,
                ordinal=1,
            )
            phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
            phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)
            phase.phase_states.create(member=member1)
            phase.phase_states.create(member=member2)
            phase.phase_states.create(member=member3)

        url = reverse(list_viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)

        assert query_count == 3


class TestGameCreateView:

    @pytest.mark.django_db
    def test_create_game_success(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "New Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
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
            "variant_id",
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
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
            "private": False,
        }
        payload2 = {
            "name": "Game 2",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
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
            "private": False,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # Since the user created the game, they should be a member
        # can_join should be False (already a member)
        # can_leave should be True (PENDING game + is a member)
        assert response.data["can_join"] is False
        assert response.data["can_leave"] is True
        assert response.data["phase_confirmed"] is False

    @pytest.mark.django_db
    def test_create_private_game_success(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Private Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": True,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["private"] is True

        # Verify game is created as private in database
        game = Game.objects.get(id=response.data["id"])
        assert game.private is True

    @pytest.mark.django_db
    def test_create_public_game_default(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Public Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["private"] is False

    @pytest.mark.django_db
    def test_create_game_default_deadline_mode_is_duration(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Default Deadline Mode Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["deadline_mode"] == DeadlineMode.DURATION

        game = Game.objects.get(id=response.data["id"])
        assert game.deadline_mode == DeadlineMode.DURATION
        assert game.fixed_deadline_time is None
        assert game.fixed_deadline_timezone is None
        assert game.movement_frequency is None
        assert game.retreat_frequency is None

    @pytest.mark.django_db
    def test_create_game_fixed_time_mode_requires_time(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Fixed Time Game Missing Time",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.FIXED_TIME,
            "fixed_deadline_timezone": "America/New_York",
            "movement_frequency": PhaseFrequency.DAILY,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fixed_deadline_time" in response.data

    @pytest.mark.django_db
    def test_create_game_fixed_time_mode_requires_timezone(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Fixed Time Game Missing Timezone",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.FIXED_TIME,
            "fixed_deadline_time": "21:00:00",
            "movement_frequency": PhaseFrequency.DAILY,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fixed_deadline_timezone" in response.data

    @pytest.mark.django_db
    def test_create_game_fixed_time_mode_requires_movement_frequency(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Fixed Time Game Missing Frequency",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.FIXED_TIME,
            "fixed_deadline_time": "21:00:00",
            "fixed_deadline_timezone": "America/New_York",
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "movement_frequency" in response.data

    @pytest.mark.django_db
    def test_create_game_fixed_time_mode_invalid_timezone(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Fixed Time Game Invalid Timezone",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.FIXED_TIME,
            "fixed_deadline_time": "21:00:00",
            "fixed_deadline_timezone": "Invalid/Timezone",
            "movement_frequency": PhaseFrequency.DAILY,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fixed_deadline_timezone" in response.data

    @pytest.mark.django_db
    def test_create_game_fixed_time_mode_success(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Fixed Time Game Success",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.FIXED_TIME,
            "fixed_deadline_time": "21:00:00",
            "fixed_deadline_timezone": "America/New_York",
            "movement_frequency": PhaseFrequency.DAILY,
            "retreat_frequency": PhaseFrequency.HOURLY,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["deadline_mode"] == DeadlineMode.FIXED_TIME
        assert response.data["fixed_deadline_time"] == "21:00:00"
        assert response.data["fixed_deadline_timezone"] == "America/New_York"
        assert response.data["movement_frequency"] == PhaseFrequency.DAILY
        assert response.data["retreat_frequency"] == PhaseFrequency.HOURLY

        game = Game.objects.get(id=response.data["id"])
        assert game.deadline_mode == DeadlineMode.FIXED_TIME
        assert game.fixed_deadline_time == time(21, 0, 0)
        assert game.fixed_deadline_timezone == "America/New_York"
        assert game.movement_frequency == PhaseFrequency.DAILY
        assert game.retreat_frequency == PhaseFrequency.HOURLY

    @pytest.mark.django_db
    def test_create_game_duration_mode_clears_fixed_time_fields(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Duration Mode Clears Fixed Fields",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.DURATION,
            "fixed_deadline_time": "21:00:00",
            "fixed_deadline_timezone": "America/New_York",
            "movement_frequency": PhaseFrequency.DAILY,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["deadline_mode"] == DeadlineMode.DURATION
        assert response.data["fixed_deadline_time"] is None
        assert response.data["fixed_deadline_timezone"] is None
        assert response.data["movement_frequency"] is None
        assert response.data["retreat_frequency"] is None

        game = Game.objects.get(id=response.data["id"])
        assert game.fixed_deadline_time is None
        assert game.fixed_deadline_timezone is None
        assert game.movement_frequency is None
        assert game.retreat_frequency is None

    @pytest.mark.django_db
    def test_retrieve_game_includes_fixed_deadline_fields(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Test Fixed Deadline Fields In Response",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.FIXED_TIME,
            "fixed_deadline_time": "09:00:00",
            "fixed_deadline_timezone": "Europe/London",
            "movement_frequency": PhaseFrequency.WEEKLY,
        }
        create_response = authenticated_client.post(url, payload, format="json")
        assert create_response.status_code == status.HTTP_201_CREATED
        game_id = create_response.data["id"]

        retrieve_url = reverse(retrieve_viewname, args=[game_id])
        response = authenticated_client.get(retrieve_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deadline_mode"] == DeadlineMode.FIXED_TIME
        assert response.data["fixed_deadline_time"] == "09:00:00"
        assert response.data["fixed_deadline_timezone"] == "Europe/London"
        assert response.data["movement_frequency"] == PhaseFrequency.WEEKLY
        assert response.data["retreat_frequency"] is None

    @pytest.mark.django_db
    def test_effective_retreat_frequency_property_fallback(self, classical_variant, db):
        game = Game.objects.create(
            name="Test Effective Retreat Frequency",
            variant=classical_variant,
            deadline_mode=DeadlineMode.FIXED_TIME,
            fixed_deadline_time=time(21, 0, 0),
            fixed_deadline_timezone="America/New_York",
            movement_frequency=PhaseFrequency.DAILY,
            retreat_frequency=None,
        )
        assert game.effective_retreat_frequency == PhaseFrequency.DAILY

        game.retreat_frequency = PhaseFrequency.HOURLY
        game.save()
        assert game.effective_retreat_frequency == PhaseFrequency.HOURLY


class TestGameCreateViewPerformance:

    @pytest.mark.django_db
    def test_create_game_query_count_small_variant(self, authenticated_client, italy_vs_germany_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Performance Test Game",
            "variant_id": italy_vs_germany_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
        }

        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        query_count = len(connection.queries)

        print(f"\nQuery count: {query_count}")
        for i, query in enumerate(connection.queries, 1):
            print(f"\nQuery {i}: {query['sql']}")

        assert query_count == 39

    @pytest.mark.django_db
    def test_create_game_query_count_large_variant(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Classical Performance Test",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
        }

        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        query_count = len(connection.queries)

        print(f"\nQuery count: {query_count}")
        for i, query in enumerate(connection.queries, 1):
            print(f"\nQuery {i}: {query['sql']}")

        assert query_count == 39


class TestGamePrivateFiltering:

    @pytest.mark.django_db
    def test_private_games_excluded_from_can_join_filter(self, authenticated_client, secondary_user, classical_variant):
        # Create a private game by secondary user
        private_game = Game.objects.create_from_template(
            classical_variant,
            name="Private Game",
            nation_assignment=NationAssignment.RANDOM,
            private=True,
        )
        private_game.members.create(user=secondary_user)

        # Create a public game by secondary user
        public_game = Game.objects.create_from_template(
            classical_variant,
            name="Public Game",
            nation_assignment=NationAssignment.RANDOM,
            private=False,
        )
        public_game.members.create(user=secondary_user)

        # Request games with can_join=true (should exclude private games)
        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"can_join": "true"})
        assert response.status_code == status.HTTP_200_OK

        game_ids = [game["id"] for game in response.data]
        assert public_game.id in game_ids
        assert private_game.id not in game_ids

    @pytest.mark.django_db
    def test_private_games_visible_in_mine_filter(self, authenticated_client, primary_user, classical_variant):
        # Create a private game by primary user
        private_game = Game.objects.create_from_template(
            classical_variant,
            name="My Private Game",
            nation_assignment=NationAssignment.RANDOM,
            private=True,
        )
        private_game.members.create(user=primary_user)

        # Request games with mine=true (should include private games for user)
        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"mine": "true"})
        assert response.status_code == status.HTTP_200_OK

        game_ids = [game["id"] for game in response.data]
        assert private_game.id in game_ids

    @pytest.mark.django_db
    def test_private_game_accessible_via_direct_link(self, authenticated_client, secondary_user, classical_variant):
        # Create a private game by secondary user
        private_game = Game.objects.create_from_template(
            classical_variant,
            name="Private Game",
            nation_assignment=NationAssignment.RANDOM,
            private=True,
        )
        private_game.members.create(user=secondary_user)

        # Authenticated user should be able to access private game via direct link
        url = reverse(retrieve_viewname, args=[private_game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == private_game.id
        assert response.data["private"] is True

    @pytest.mark.django_db
    def test_game_with_48_hour_phase_duration(self, authenticated_client, classical_variant, primary_user):
        from common.constants import MovementPhaseDuration
        from datetime import timedelta
        from django.utils import timezone

        game = Game.objects.create(
            name="48 Hour Game",
            variant=classical_variant,
            movement_phase_duration=MovementPhaseDuration.FORTY_EIGHT_HOURS,
        )
        game.members.create(user=primary_user)

        assert game.movement_phase_duration_seconds == 48 * 60 * 60

        game.status = GameStatus.PENDING
        game.save()

        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.PENDING,
            ordinal=1,
        )

        game.status = GameStatus.ACTIVE
        phase.status = PhaseStatus.ACTIVE
        now = timezone.now()
        phase.scheduled_resolution = now + timedelta(seconds=game.movement_phase_duration_seconds)
        phase.save()
        game.save()

        expected_resolution = now + timedelta(hours=48)
        assert abs((phase.scheduled_resolution - expected_resolution).total_seconds()) < 1

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["movement_phase_duration"] == "48 hours"

    @pytest.mark.django_db
    def test_game_with_one_week_phase_duration(self, authenticated_client, active_game_with_phase_state):
        game = active_game_with_phase_state
        phase = game.current_phase
        now = timezone.now()

        game.movement_phase_duration = MovementPhaseDuration.ONE_WEEK
        phase.scheduled_resolution = now + timedelta(seconds=game.movement_phase_duration_seconds)
        phase.save()
        game.save()

        expected_resolution = now + timedelta(weeks=1)
        assert abs((phase.scheduled_resolution - expected_resolution).total_seconds()) < 1

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["movement_phase_duration"] == "1 week"


class TestGameDurationOptions:

    @pytest.mark.django_db
    @pytest.mark.parametrize("duration,expected_seconds", [
        ("1 hour", 3600),
        ("12 hours", 43200),
        ("24 hours", 86400),
        ("48 hours", 172800),
        ("3 days", 259200),
        ("4 days", 345600),
        ("1 week", 604800),
        ("2 weeks", 1209600),
    ])
    def test_game_duration_options(self, authenticated_client, classical_variant, duration, expected_seconds):
        url = reverse(create_viewname)
        payload = {
            "name": f"Test Game {duration}",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "movement_phase_duration": duration,
            "private": False,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.movement_phase_duration == duration
        assert game.movement_phase_duration_seconds == expected_seconds


class TestRetreatPhaseDuration:

    @pytest.mark.django_db
    def test_create_game_with_retreat_phase_duration(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Game with Retreat Duration",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "movement_phase_duration": MovementPhaseDuration.TWENTY_FOUR_HOURS,
            "retreat_phase_duration": MovementPhaseDuration.TWELVE_HOURS,
            "private": False,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.movement_phase_duration == MovementPhaseDuration.TWENTY_FOUR_HOURS
        assert game.retreat_phase_duration == MovementPhaseDuration.TWELVE_HOURS
        assert response.data["retreat_phase_duration"] == MovementPhaseDuration.TWELVE_HOURS

    @pytest.mark.django_db
    def test_create_game_retreat_duration_defaults_to_none(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Game without Retreat Duration",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "movement_phase_duration": MovementPhaseDuration.FORTY_EIGHT_HOURS,
            "private": False,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.retreat_phase_duration is None
        assert game.retreat_phase_duration_seconds == game.movement_phase_duration_seconds

    @pytest.mark.django_db
    def test_retreat_phase_duration_seconds_fallback(self, classical_variant):
        game = Game.objects.create(
            name="Fallback Test Game",
            variant=classical_variant,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            retreat_phase_duration=None,
        )
        assert game.retreat_phase_duration_seconds == game.movement_phase_duration_seconds
        assert game.retreat_phase_duration_seconds == 24 * 60 * 60

    @pytest.mark.django_db
    def test_retreat_phase_duration_seconds_override(self, classical_variant):
        game = Game.objects.create(
            name="Override Test Game",
            variant=classical_variant,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            retreat_phase_duration=MovementPhaseDuration.TWELVE_HOURS,
        )
        assert game.movement_phase_duration_seconds == 24 * 60 * 60
        assert game.retreat_phase_duration_seconds == 12 * 60 * 60

    @pytest.mark.django_db
    def test_get_phase_duration_seconds_movement(self, classical_variant):
        from common.constants import PhaseType
        game = Game.objects.create(
            name="Phase Duration Test",
            variant=classical_variant,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            retreat_phase_duration=MovementPhaseDuration.TWELVE_HOURS,
        )
        assert game.get_phase_duration_seconds(PhaseType.MOVEMENT) == 24 * 60 * 60

    @pytest.mark.django_db
    def test_get_phase_duration_seconds_retreat(self, classical_variant):
        from common.constants import PhaseType
        game = Game.objects.create(
            name="Phase Duration Test",
            variant=classical_variant,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            retreat_phase_duration=MovementPhaseDuration.TWELVE_HOURS,
        )
        assert game.get_phase_duration_seconds(PhaseType.RETREAT) == 12 * 60 * 60

    @pytest.mark.django_db
    def test_get_phase_duration_seconds_adjustment(self, classical_variant):
        from common.constants import PhaseType
        game = Game.objects.create(
            name="Phase Duration Test",
            variant=classical_variant,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            retreat_phase_duration=MovementPhaseDuration.TWELVE_HOURS,
        )
        assert game.get_phase_duration_seconds(PhaseType.ADJUSTMENT) == 12 * 60 * 60

    @pytest.mark.django_db
    def test_retreat_phase_duration_in_api_response(self, authenticated_client, classical_variant):
        game = Game.objects.create_from_template(
            classical_variant,
            name="API Response Test",
            nation_assignment=NationAssignment.RANDOM,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            retreat_phase_duration=MovementPhaseDuration.TWELVE_HOURS,
            private=False,
        )
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["retreat_phase_duration"] == MovementPhaseDuration.TWELVE_HOURS


class TestGameInfinitePhaseDuration:

    @pytest.mark.django_db
    def test_movement_phase_duration_can_be_none(self, classical_variant):
        game = Game.objects.create(
            name="Infinite Duration Game",
            variant=classical_variant,
            movement_phase_duration=None,
        )
        assert game.movement_phase_duration is None

    @pytest.mark.django_db
    def test_movement_phase_duration_seconds_returns_none_when_duration_is_none(self, classical_variant):
        game = Game.objects.create(
            name="Infinite Duration Game",
            variant=classical_variant,
            movement_phase_duration=None,
        )
        assert game.movement_phase_duration_seconds is None

    @pytest.mark.django_db
    def test_game_start_with_infinite_duration_sets_scheduled_resolution_to_none(self, classical_variant, primary_user):

        game = Game.objects.create(
            name="Infinite Duration Game",
            variant=classical_variant,
            movement_phase_duration=None,
            status=GameStatus.PENDING,
        )
        game.members.create(user=primary_user)

        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.PENDING,
            ordinal=1,
        )

        with patch.object(adjudication_service, "start", return_value={"options": {}}):
            game.start()

        phase.refresh_from_db()
        assert phase.scheduled_resolution is None
        assert phase.status == PhaseStatus.ACTIVE
        assert game.status == GameStatus.ACTIVE

    @pytest.mark.django_db
    def test_game_sandbox_field_defaults_to_false(self, classical_variant):
        game = Game.objects.create(
            name="Regular Game",
            variant=classical_variant,
        )
        assert game.sandbox is False

    @pytest.mark.django_db
    def test_game_can_be_created_as_sandbox(self, classical_variant):
        game = Game.objects.create(
            name="Sandbox Game",
            variant=classical_variant,
            sandbox=True,
        )
        assert game.sandbox is True


class TestSandboxGameCreation:

    @pytest.mark.django_db
    def test_create_sandbox_game_success(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_create_sandbox_game_sets_sandbox_true(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.sandbox is True

    @pytest.mark.django_db
    def test_create_sandbox_game_sets_private_true(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.private is True

    @pytest.mark.django_db
    def test_create_sandbox_game_sets_infinite_duration(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.movement_phase_duration is None

    @pytest.mark.django_db
    def test_create_sandbox_game_sets_ordered_nation_assignment(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.nation_assignment == NationAssignment.ORDERED

    @pytest.mark.django_db
    def test_create_sandbox_game_creates_multiple_members(self, authenticated_client, classical_variant, primary_user):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.members.count() == 7
        assert all(member.user == primary_user for member in game.members.all())

    @pytest.mark.django_db
    def test_create_sandbox_game_does_not_create_channels(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.channels.count() == 0

    @pytest.mark.django_db
    def test_create_sandbox_game_starts_immediately(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.status == GameStatus.ACTIVE

    @pytest.mark.django_db
    def test_create_sandbox_game_creates_phase_states(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        current_phase = game.current_phase
        assert current_phase.phase_states.count() == 7

    @pytest.mark.django_db
    def test_create_sandbox_game_missing_name(self, authenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_create_sandbox_game_missing_variant_id(self, authenticated_client):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "variant_id" in response.data

    @pytest.mark.django_db
    def test_create_sandbox_game_invalid_variant_id(self, authenticated_client):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": "non-existent-variant",
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "variant_id" in response.data

    @pytest.mark.django_db
    def test_create_sandbox_game_unauthenticated(self, unauthenticated_client, classical_variant):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "My Sandbox Game",
            "variant_id": classical_variant.id,
        }
        response = unauthenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSandboxGameCreateViewPerformance:

    @pytest.mark.django_db
    def test_create_sandbox_game_query_count_small_variant(
        self, authenticated_client, italy_vs_germany_variant, adjudication_data_italy_vs_germany
    ):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "Sandbox Performance Test",
            "variant_id": italy_vs_germany_variant.id,
        }

        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            with patch("adjudication.service.start") as mock_start:
                mock_start.return_value = adjudication_data_italy_vs_germany
                response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        query_count = len(connection.queries)

        print(f"\nQuery count (small variant): {query_count}")
        for i, query in enumerate(connection.queries, 1):
            print(f"\nQuery {i}: {query['sql']}")

        assert query_count == 44

    @pytest.mark.django_db
    def test_create_sandbox_game_query_count_large_variant(
        self, authenticated_client, classical_variant, adjudication_data_classical
    ):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "Classical Sandbox Performance Test",
            "variant_id": classical_variant.id,
        }

        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            with patch("adjudication.service.start") as mock_start:
                mock_start.return_value = adjudication_data_classical
                response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        query_count = len(connection.queries)

        print(f"\nQuery count (large variant): {query_count}")
        for i, query in enumerate(connection.queries, 1):
            print(f"\nQuery {i}: {query['sql']}")

        assert query_count == 44


class TestSandboxGameFiltering:

    @pytest.mark.django_db
    def test_sandbox_games_excluded_from_default_list(self, authenticated_client, primary_user, classical_variant):
        regular_game = Game.objects.create_from_template(
            classical_variant,
            name="Regular Game",
            nation_assignment=NationAssignment.RANDOM,
            private=False,
        )
        regular_game.members.create(user=primary_user)

        sandbox_game = Game.objects.create_from_template(
            classical_variant,
            name="Sandbox Game",
            sandbox=True,
            private=True,
            nation_assignment=NationAssignment.ORDERED,
            movement_phase_duration=None,
        )
        sandbox_game.members.create(user=primary_user)

        url = reverse(list_viewname)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        game_ids = [game["id"] for game in response.data]
        assert regular_game.id in game_ids
        assert sandbox_game.id not in game_ids

    @pytest.mark.django_db
    def test_sandbox_games_included_when_filter_true(self, authenticated_client, primary_user, classical_variant):
        regular_game = Game.objects.create_from_template(
            classical_variant,
            name="Regular Game",
            nation_assignment=NationAssignment.RANDOM,
            private=False,
        )
        regular_game.members.create(user=primary_user)

        sandbox_game = Game.objects.create_from_template(
            classical_variant,
            name="Sandbox Game",
            sandbox=True,
            private=True,
            nation_assignment=NationAssignment.ORDERED,
            movement_phase_duration=None,
        )
        sandbox_game.members.create(user=primary_user)

        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"sandbox": "true"})
        assert response.status_code == status.HTTP_200_OK

        game_ids = [game["id"] for game in response.data]
        assert sandbox_game.id in game_ids
        assert regular_game.id not in game_ids

    @pytest.mark.django_db
    def test_sandbox_filter_false_excludes_sandbox_games(self, authenticated_client, primary_user, classical_variant):
        regular_game = Game.objects.create_from_template(
            classical_variant,
            name="Regular Game",
            nation_assignment=NationAssignment.RANDOM,
            private=False,
        )
        regular_game.members.create(user=primary_user)

        sandbox_game = Game.objects.create_from_template(
            classical_variant,
            name="Sandbox Game",
            sandbox=True,
            private=True,
            nation_assignment=NationAssignment.ORDERED,
            movement_phase_duration=None,
        )
        sandbox_game.members.create(user=primary_user)

        url = reverse(list_viewname)
        response = authenticated_client.get(url, {"sandbox": "false"})
        assert response.status_code == status.HTTP_200_OK

        game_ids = [game["id"] for game in response.data]
        assert regular_game.id in game_ids
        assert sandbox_game.id not in game_ids


class TestGameAdminQueryPerformance:

    @pytest.mark.django_db
    def test_admin_changelist_query_count_simple(
        self, authenticated_client, pending_game_created_by_primary_user, primary_user
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        url = "/admin/game/game/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200
        query_count = len(connection.queries)
        assert query_count == 7

    @pytest.mark.django_db
    def test_admin_changelist_query_count_with_multiple_games_and_phases(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        classical_england_nation,
        classical_edinburgh_province,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        for i in range(4):
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

        url = "/admin/game/game/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200
        query_count = len(connection.queries)
        assert query_count == 7

    @pytest.mark.django_db
    def test_admin_changelist_query_count_with_many_games(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        classical_england_nation,
        classical_edinburgh_province,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        for i in range(10):
            game = Game.objects.create(
                name=f"Game {i}",
                variant=classical_variant,
                status=GameStatus.ACTIVE,
            )
            game.members.create(user=primary_user, nation=classical_england_nation)

            phase_count = i % 4
            for j in range(phase_count):
                phase = game.phases.create(
                    game=game,
                    variant=game.variant,
                    season="Spring" if j % 2 == 0 else "Fall",
                    year=1901 + (j // 2),
                    type="Movement",
                    status=PhaseStatus.ACTIVE if j == phase_count - 1 else PhaseStatus.COMPLETED,
                    ordinal=j + 1,
                )
                phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
                phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

        url = "/admin/game/game/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200
        query_count = len(connection.queries)
        assert query_count <= 7


class TestGameMaster:

    @pytest.mark.django_db
    def test_create_game_sets_creator_as_game_master(self, authenticated_client, classical_variant, primary_user):
        url = reverse(create_viewname)
        payload = {
            "name": "Game Master Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        creator_member = game.members.get(user=primary_user)
        assert creator_member.is_game_master is True

    @pytest.mark.django_db
    def test_create_game_api_response_includes_is_game_master(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = {
            "name": "Game Master API Test",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        assert len(response.data["members"]) == 1
        assert response.data["members"][0]["is_game_master"] is True

    @pytest.mark.django_db
    def test_retrieve_game_shows_game_master_in_members(
        self, authenticated_client, pending_game_created_by_primary_user
    ):
        url = reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert len(response.data["members"]) == 1
        assert response.data["members"][0]["is_game_master"] is True

    @pytest.mark.django_db
    def test_sandbox_game_has_no_game_master(self, authenticated_client, classical_variant, primary_user):
        url = reverse(sandbox_create_viewname)
        payload = {
            "name": "Sandbox No GM Test",
            "variant_id": classical_variant.id,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.members.filter(is_game_master=True).count() == 0
        assert all(member.is_game_master is False for member in game.members.all())

    @pytest.mark.django_db
    def test_clone_to_sandbox_has_no_game_master(
        self, authenticated_client, active_game_with_phase_state, adjudication_data_classical, primary_user
    ):
        from unittest.mock import patch
        url = reverse("game-clone-to-sandbox", args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED

        game = Game.objects.get(id=response.data["id"])
        assert game.members.filter(is_game_master=True).count() == 0
        assert all(member.is_game_master is False for member in game.members.all())


clone_to_sandbox_viewname = "game-clone-to-sandbox"


class TestGameCloneToSandbox:

    @pytest.mark.django_db
    def test_clone_to_sandbox_success(
        self, authenticated_client, active_game_with_phase_state, adjudication_data_classical
    ):
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["sandbox"] is True
        assert response.data["private"] is True

    @pytest.mark.django_db
    def test_clone_to_sandbox_creates_correct_name(
        self, authenticated_client, active_game_with_phase_state, adjudication_data_classical
    ):
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        expected_name = f"{active_game_with_phase_state.name} (Sandbox)"
        assert response.data["name"] == expected_name

    @pytest.mark.django_db
    def test_clone_to_sandbox_copies_units(
        self, authenticated_client, active_game_with_phase_state, adjudication_data_classical
    ):
        source_units_count = active_game_with_phase_state.current_phase.units.count()
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        new_game = Game.objects.get(id=response.data["id"])
        assert new_game.current_phase.units.count() == source_units_count

    @pytest.mark.django_db
    def test_clone_to_sandbox_copies_supply_centers(
        self, authenticated_client, active_game_with_phase_state, adjudication_data_classical
    ):
        source_sc_count = active_game_with_phase_state.current_phase.supply_centers.count()
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        new_game = Game.objects.get(id=response.data["id"])
        assert new_game.current_phase.supply_centers.count() == source_sc_count

    @pytest.mark.django_db
    def test_clone_to_sandbox_preserves_phase_info(
        self, authenticated_client, active_game_with_phase_state, adjudication_data_classical
    ):
        source_phase = active_game_with_phase_state.current_phase
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        new_game = Game.objects.get(id=response.data["id"])
        new_phase = new_game.current_phase
        assert new_phase.season == source_phase.season
        assert new_phase.year == source_phase.year
        assert new_phase.type == source_phase.type

    @pytest.mark.django_db
    def test_clone_to_sandbox_creates_all_members_for_user(
        self, authenticated_client, active_game_with_phase_state, primary_user, adjudication_data_classical
    ):
        nations_count = active_game_with_phase_state.variant.nations.count()
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        new_game = Game.objects.get(id=response.data["id"])
        assert new_game.members.count() == nations_count
        assert all(m.user == primary_user for m in new_game.members.all())

    @pytest.mark.django_db
    def test_clone_to_sandbox_game_is_active(
        self, authenticated_client, active_game_with_phase_state, adjudication_data_classical
    ):
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == GameStatus.ACTIVE

    @pytest.mark.django_db
    def test_clone_to_sandbox_deletes_oldest_when_at_limit(
        self, authenticated_client, primary_user, classical_variant, adjudication_data_classical,
        active_game_with_phase_state
    ):
        sandboxes = []
        for i in range(3):
            sandbox = Game.objects.create_from_template(
                classical_variant,
                name=f"Existing Sandbox {i}",
                sandbox=True,
                private=True,
                nation_assignment=NationAssignment.ORDERED,
                movement_phase_duration=None,
            )
            sandbox.members.create(user=primary_user)
            sandboxes.append(sandbox)

        oldest_sandbox_id = sandboxes[0].id

        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        with patch("adjudication.service.start") as mock_start:
            mock_start.return_value = adjudication_data_classical
            response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert not Game.objects.filter(id=oldest_sandbox_id).exists()

    @pytest.mark.django_db
    def test_clone_to_sandbox_unauthenticated(
        self, unauthenticated_client, active_game_with_phase_state
    ):
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        response = unauthenticated_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_clone_to_sandbox_non_member(
        self, authenticated_client_for_secondary_user, active_game_with_phase_state
    ):
        url = reverse(clone_to_sandbox_viewname, args=[active_game_with_phase_state.id])
        response = authenticated_client_for_secondary_user.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_clone_to_sandbox_pending_game(
        self, authenticated_client, pending_game_created_by_primary_user
    ):
        url = reverse(clone_to_sandbox_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_clone_to_sandbox_game_not_found(self, authenticated_client):
        url = reverse(clone_to_sandbox_viewname, args=["non-existent-game"])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


pause_viewname = "game-pause"
unpause_viewname = "game-unpause"


class TestGamePauseUnpause:

    @pytest.mark.django_db
    def test_pause_game_success(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(pause_viewname, args=[game.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_paused"] is True
        assert response.data["paused_at"] is not None

    @pytest.mark.django_db
    def test_pause_game_non_game_master_forbidden(self, api_client, active_game_with_gm, secondary_user):
        game = active_game_with_gm()
        game.members.create(user=secondary_user)
        api_client.force_authenticate(user=secondary_user)
        url = reverse(pause_viewname, args=[game.id])
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_pause_game_non_member_forbidden(self, api_client, active_game_with_gm, secondary_user):
        game = active_game_with_gm()
        api_client.force_authenticate(user=secondary_user)
        url = reverse(pause_viewname, args=[game.id])
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_pause_game_unauthenticated(self, unauthenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(pause_viewname, args=[game.id])
        response = unauthenticated_client.patch(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_pause_pending_game_forbidden(self, authenticated_client, pending_game_with_gm):
        game = pending_game_with_gm()
        url = reverse(pause_viewname, args=[game.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_pause_already_paused_game_returns_400(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(pause_viewname, args=[game.id])
        authenticated_client.patch(url)
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_unpause_game_success(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        pause_url = reverse(pause_viewname, args=[game.id])
        authenticated_client.patch(pause_url)
        unpause_url = reverse(unpause_viewname, args=[game.id])
        response = authenticated_client.patch(unpause_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_paused"] is False
        assert response.data["paused_at"] is None

    @pytest.mark.django_db
    def test_unpause_game_recalculates_deadline(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        phase = game.current_phase
        original_deadline = phase.scheduled_resolution

        pause_url = reverse(pause_viewname, args=[game.id])
        authenticated_client.patch(pause_url)

        game.refresh_from_db()
        paused_time = game.paused_at

        simulated_unpause_time = paused_time + timedelta(hours=2)
        with patch("game.models.timezone.now") as mock_now:
            mock_now.return_value = simulated_unpause_time
            unpause_url = reverse(unpause_viewname, args=[game.id])
            authenticated_client.patch(unpause_url)

        phase.refresh_from_db()
        expected_deadline = original_deadline + timedelta(hours=2)
        assert abs((phase.scheduled_resolution - expected_deadline).total_seconds()) < 1

    @pytest.mark.django_db
    def test_unpause_not_paused_game_returns_400(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(unpause_viewname, args=[game.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_unpause_game_non_game_master_forbidden(
        self, authenticated_client, api_client, active_game_with_gm, secondary_user
    ):
        game = active_game_with_gm()
        pause_url = reverse(pause_viewname, args=[game.id])
        authenticated_client.patch(pause_url)
        game.members.create(user=secondary_user)
        api_client.force_authenticate(user=secondary_user)
        unpause_url = reverse(unpause_viewname, args=[game.id])
        response = api_client.patch(unpause_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_paused_game_excluded_from_due_phases(self, db, active_game_with_gm):
        from phase.models import Phase

        game = active_game_with_gm()
        phase = game.current_phase
        phase.scheduled_resolution = timezone.now() - timedelta(minutes=5)
        phase.save()

        assert phase in Phase.objects.filter_due_phases()

        game.paused_at = timezone.now()
        game.save()

        assert phase not in Phase.objects.filter_due_phases()

    @pytest.mark.django_db
    def test_is_paused_property(self, db, classical_variant):
        game = Game.objects.create_from_template(
            classical_variant,
            name="Pause Property Test",
        )
        assert game.is_paused is False

        game.paused_at = timezone.now()
        game.save()
        assert game.is_paused is True

        game.paused_at = None
        game.save()
        assert game.is_paused is False

    @pytest.mark.django_db
    def test_pause_fields_in_game_list_response(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(list_viewname)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        game_data = next((g for g in response.data if g["id"] == game.id), None)
        assert game_data is not None
        assert "is_paused" in game_data
        assert "paused_at" in game_data
        assert game_data["is_paused"] is False
        assert game_data["paused_at"] is None

    @pytest.mark.django_db
    def test_pause_fields_in_game_retrieve_response(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "is_paused" in response.data
        assert "paused_at" in response.data
        assert response.data["is_paused"] is False
        assert response.data["paused_at"] is None


extend_deadline_viewname = "game-extend-deadline"


class TestGameExtendDeadline:

    @pytest.mark.django_db
    def test_extend_deadline_success(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        phase = game.current_phase
        original_deadline = phase.scheduled_resolution

        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        phase.refresh_from_db()
        expected_deadline = original_deadline + timedelta(hours=1)
        assert abs((phase.scheduled_resolution - expected_deadline).total_seconds()) < 1

    @pytest.mark.django_db
    def test_extend_deadline_24_hours(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        phase = game.current_phase
        original_deadline = phase.scheduled_resolution

        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(
            url, {"duration": MovementPhaseDuration.TWENTY_FOUR_HOURS}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        phase.refresh_from_db()
        expected_deadline = original_deadline + timedelta(hours=24)
        assert abs((phase.scheduled_resolution - expected_deadline).total_seconds()) < 1

    @pytest.mark.django_db
    def test_extend_deadline_non_game_master_forbidden(self, api_client, active_game_with_gm, secondary_user):
        game = active_game_with_gm()
        game.members.create(user=secondary_user)
        api_client.force_authenticate(user=secondary_user)
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = api_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_extend_deadline_non_member_forbidden(self, api_client, active_game_with_gm, secondary_user):
        game = active_game_with_gm()
        api_client.force_authenticate(user=secondary_user)
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = api_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_extend_deadline_unauthenticated(self, unauthenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = unauthenticated_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_extend_deadline_pending_game_forbidden(self, authenticated_client, pending_game_with_gm):
        game = pending_game_with_gm()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_extend_deadline_paused_game_returns_400(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        pause_url = reverse(pause_viewname, args=[game.id])
        authenticated_client.patch(pause_url)

        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_extend_deadline_invalid_duration_returns_400(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(
            url, {"duration": "invalid_duration"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_extend_deadline_missing_duration_returns_400(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_extend_deadline_multiple_times(self, authenticated_client, active_game_with_gm):
        game = active_game_with_gm()
        phase = game.current_phase
        original_deadline = phase.scheduled_resolution

        url = reverse(extend_deadline_viewname, args=[game.id])
        authenticated_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        authenticated_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )

        phase.refresh_from_db()
        expected_deadline = original_deadline + timedelta(hours=2)
        assert abs((phase.scheduled_resolution - expected_deadline).total_seconds()) < 1


pause_viewname = "game-pause"
unpause_viewname = "game-unpause"


class TestGamePauseNotification:

    @pytest.mark.django_db
    def test_pause_game_sends_notification(
        self,
        authenticated_client,
        active_game_with_gm,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game = active_game_with_gm()
        mock_send_notification_to_users.reset_mock()

        url = reverse(pause_viewname, args=[game.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK

        mock_send_notification_to_users.assert_called_once()
        call_kwargs = mock_send_notification_to_users.call_args[1]
        assert call_kwargs["notification_type"] == "game_paused"
        assert "Game paused by Game Master" in call_kwargs["body"]
        assert call_kwargs["data"]["game_id"] == str(game.id)


class TestGameUnpauseNotification:

    @pytest.mark.django_db
    def test_unpause_game_sends_notification(
        self,
        authenticated_client,
        active_game_with_gm,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game = active_game_with_gm()
        game.pause()
        game.save()
        mock_send_notification_to_users.reset_mock()

        url = reverse(unpause_viewname, args=[game.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK

        mock_send_notification_to_users.assert_called_once()
        call_kwargs = mock_send_notification_to_users.call_args[1]
        assert call_kwargs["notification_type"] == "game_resumed"
        assert "Game resumed by Game Master" in call_kwargs["body"]
        assert "New deadline:" in call_kwargs["body"]


class TestGameExtendDeadlineNotification:

    @pytest.mark.django_db
    def test_extend_deadline_sends_notification(
        self,
        authenticated_client,
        active_game_with_gm,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game = active_game_with_gm()
        mock_send_notification_to_users.reset_mock()

        url = reverse(extend_deadline_viewname, args=[game.id])
        response = authenticated_client.patch(
            url, {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        mock_send_notification_to_users.assert_called_once()
        call_kwargs = mock_send_notification_to_users.call_args[1]
        assert call_kwargs["notification_type"] == "game_deadline_extended"
        assert "Deadline extended by Game Master" in call_kwargs["body"]


class TestGameNmrExtensions:

    @pytest.mark.django_db
    def test_create_game_with_nmr_extensions(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        response = authenticated_client.post(url, {
            "name": "Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": "random",
            "movement_phase_duration": "24 hours",
            "private": False,
            "nmr_extensions_allowed": 2,
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["nmr_extensions_allowed"] == 2

    @pytest.mark.django_db
    def test_create_game_without_nmr_extensions_defaults_to_zero(
        self, authenticated_client, classical_variant
    ):
        url = reverse(create_viewname)
        response = authenticated_client.post(url, {
            "name": "Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": "random",
            "movement_phase_duration": "24 hours",
            "private": False,
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["nmr_extensions_allowed"] == 0

    @pytest.mark.django_db
    def test_create_game_nmr_extensions_over_max_rejected(
        self, authenticated_client, classical_variant
    ):
        url = reverse(create_viewname)
        response = authenticated_client.post(url, {
            "name": "Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": "random",
            "movement_phase_duration": "24 hours",
            "private": False,
            "nmr_extensions_allowed": 3,
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_game_nmr_extensions_negative_rejected(
        self, authenticated_client, classical_variant
    ):
        url = reverse(create_viewname)
        response = authenticated_client.post(url, {
            "name": "Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": "random",
            "movement_phase_duration": "24 hours",
            "private": False,
            "nmr_extensions_allowed": -1,
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_game_start_initializes_member_extensions(
        self, authenticated_client, active_game_with_gm
    ):
        game = active_game_with_gm(nmr_extensions_allowed=2)
        for member in game.members.all():
            assert member.nmr_extensions_remaining == 2

    @pytest.mark.django_db
    def test_game_start_with_zero_extensions(
        self, authenticated_client, active_game_with_gm
    ):
        game = active_game_with_gm(nmr_extensions_allowed=0)
        for member in game.members.all():
            assert member.nmr_extensions_remaining == 0

    @pytest.mark.django_db
    def test_member_serializer_includes_extensions_remaining(
        self, authenticated_client, active_game_with_gm
    ):
        game = active_game_with_gm(nmr_extensions_allowed=1)
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for member in response.data["members"]:
            assert "nmr_extensions_remaining" in member
            assert member["nmr_extensions_remaining"] == 1
