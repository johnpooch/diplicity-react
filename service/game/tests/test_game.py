import json

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status, exceptions
from game import models
from .base import BaseTestCase
from unittest.mock import MagicMock, patch
from game.services import GameService

User = get_user_model()


class TestGameList(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game1 = self.create_game(self.user, "Game 1")
        self.game2 = self.create_game(self.other_user, "Game 2")
        member = self.game1.members.first()
        member.nation = "England"
        member.save()
        member = self.game2.members.first()
        member.nation = "France"
        member.save()

    def create_request(self, params=None):
        url = reverse("game-list")
        return self.client.get(url, params)

    def test_unauthenticated(self):
        self.client.logout()
        response = self.create_request()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_filter(self):
        response = self.create_request({"invalid_filter": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_all_games(self):
        response = self.create_request()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_my_games(self):
        response = self.create_request({"mine": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Game 1")

    def test_can_join(self):
        response = self.create_request({"can_join": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Game 2")

    def test_response_structure(self):
        response = self.create_request()
        game = next(game for game in response.data if game["name"] == "Game 1")
        unit = game["current_phase"]["units"][0]
        supply_center = game["current_phase"]["supply_centers"][0]
        member = game["members"][0]

        self.assertEqual(game["id"], self.game1.id)
        self.assertEqual(game["name"], "Game 1")
        self.assertEqual(game["status"], "pending")
        self.assertEqual(game["movement_phase_duration"], "24 hours")
        self.assertEqual(game["can_join"], False)
        self.assertEqual(game["can_leave"], True)

        self.assertEqual(game["current_phase"]["type"], "Movement")
        self.assertEqual(game["current_phase"]["ordinal"], 1)
        self.assertEqual(game["current_phase"]["season"], "Spring")
        self.assertEqual(game["current_phase"]["year"], "1901")
        self.assertEqual(game["current_phase"]["name"], "Spring 1901, Movement")
        self.assertIsInstance(game["current_phase"]["units"], list)
        self.assertIsInstance(game["current_phase"]["supply_centers"], list)
        self.assertIn("remaining_time", game["current_phase"])

        self.assertEqual(unit["type"], "Fleet")

        self.assertEqual(unit["nation"]["name"], "England")
        self.assertEqual(unit["nation"]["color"], "#2196F3")

        self.assertEqual(unit["province"]["id"], "edi")
        self.assertEqual(unit["province"]["name"], "Edinburgh")
        self.assertEqual(unit["province"]["type"], "coastal")
        self.assertEqual(unit["province"]["supply_center"], True)

        self.assertEqual(supply_center["nation"]["name"], "England")
        self.assertEqual(supply_center["nation"]["color"], "#2196F3")

        self.assertEqual(supply_center["province"]["id"], "edi")
        self.assertEqual(supply_center["province"]["name"], "Edinburgh")
        self.assertEqual(supply_center["province"]["type"], "coastal")
        self.assertEqual(supply_center["province"]["supply_center"], True)

        self.assertEqual(game["variant"]["id"], self.variant.id)
        self.assertEqual(game["variant"]["name"], self.variant.name)
        self.assertEqual(game["variant"]["description"], self.variant.description)
        self.assertEqual(game["variant"]["author"], self.variant.author)
        self.assertIsInstance(game["variant"]["nations"], list)
        self.assertEqual(game["variant"]["nations"][0]["name"], "England")
        self.assertEqual(game["variant"]["nations"][0]["color"], "#2196F3")

        self.assertIn("members", game)
        self.assertEqual(len(game["members"]), 1)

        self.assertEqual(member["id"], self.user.id)
        self.assertEqual(member["username"], self.user.username)
        self.assertEqual(member["name"], self.user.profile.name)
        self.assertEqual(member["picture"], self.user.profile.picture)
        self.assertEqual(member["nation"], "England")  # Updated assertion
        self.assertEqual(member["is_current_user"], True)


class TestGameRetrieve(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1")

    def test_retrieve_game(self):
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.game.id)
        self.assertEqual(response.data["name"], self.game.name)

    def test_retrieve_game_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 401)

    def test_retrieve_game_not_found(self):
        response = self.client.get(reverse("game-retrieve", args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_retrieve_game_response_structure(self):
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", response.data)
        self.assertIn("name", response.data)
        self.assertIn("status", response.data)
        self.assertIn("movement_phase_duration", response.data)
        self.assertIn("can_join", response.data)
        self.assertIn("can_leave", response.data)
        self.assertIn("current_phase", response.data)
        self.assertIn("variant", response.data)
        self.assertIn("members", response.data)


class TestGameCreate(BaseTestCase):

    def create_request(self, payload):
        return self.client.post(
            reverse("game-create"), payload, content_type="application/json"
        )

    def test_create_game_success(self):
        payload = {"name": "New Game", "variant": self.variant.id}
        response = self.create_request(payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["name"], payload["name"])

        # Verify that a phase is created in a pending state
        game = models.Game.objects.get(id=response.data["id"])
        self.assertEqual(game.phases.count(), 1)
        phase = game.phases.first()
        self.assertEqual(phase.status, models.Phase.PENDING)
        self.assertEqual(phase.season, self.variant.start["season"])
        self.assertEqual(phase.year, self.variant.start["year"])
        self.assertEqual(phase.type, self.variant.start["type"])

        # Verify that units are created for the phase
        units = models.Unit.objects.filter(phase=phase)
        self.assertEqual(units.count(), len(self.variant.start["units"]))
        for unit_data in self.variant.start["units"]:
            self.assertTrue(
                units.filter(
                    type=unit_data["type"].lower(),
                    nation=unit_data["nation"],
                    province=unit_data["province"],
                ).exists()
            )

        # Verify that supply centers are created for the phase
        supply_centers = models.SupplyCenter.objects.filter(phase=phase)
        self.assertEqual(
            supply_centers.count(), len(self.variant.start["supply_centers"])
        )
        for sc_data in self.variant.start["supply_centers"]:
            self.assertTrue(
                supply_centers.filter(
                    nation=sc_data["nation"],
                    province=sc_data["province"],
                ).exists()
            )

    def test_create_game_missing_name(self):
        payload = {"variant": self.variant.id}
        response = self.create_request(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_game_missing_variant(self):
        payload = {"name": "New Game"}
        response = self.create_request(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("variant", response.data)

    def test_create_game_unauthenticated(self):
        self.client.logout()
        payload = {"name": "New Game", "variant": self.variant.id}
        response = self.create_request(payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestGameJoin(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(
            self.other_user, "Game 1", status=models.Game.PENDING
        )

    def create_request(self, game_id):
        url = reverse("game-join", args=[game_id])
        return self.client.post(url)

    def test_unauthenticated(self):
        self.client.logout()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_join_game_success(self):
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.game.id)
        self.assertEqual(response.data["name"], self.game.name)

    def test_join_game_already_member(self):
        self.game.members.create(user=self.user)
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_join_game_non_pending(self):
        self.game.status = "active"
        self.game.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_join_game_not_found(self):
        response = self.create_request(999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestGameLeave(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(
            self.other_user, "Game 1", status=models.Game.PENDING
        )
        self.member = self.game.members.create(user=self.user)

    def create_request(self, game_id):
        url = reverse("game-leave", args=[game_id])
        return self.client.delete(url)

    def test_unauthenticated(self):
        self.client.logout()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_leave_game_success(self):
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.game.members.filter(user=self.user).exists())

    def test_leave_game_not_a_member(self):
        self.member.delete()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leave_game_non_pending(self):
        self.game.status = models.Game.ACTIVE
        self.game.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_leave_game_not_found(self):
        response = self.create_request(999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestGameStart(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.PENDING)
        self.adjudication_service_mock = MagicMock()
        self.apply_async_patch = patch("game.tasks.notify_task.apply_async")
        self.mock_apply_async = self.apply_async_patch.start()
        self.addCleanup(self.apply_async_patch.stop)
        self.service = GameService(
            user=self.user,
            adjudication_service=self.adjudication_service_mock,
        )

    def test_start_game_success(self):
        # Mock adjudication service response
        self.adjudication_service_mock.start.return_value = {
            "phase": {
                "season": "Spring",
                "year": 1901,
                "type": "Movement",
            },
            "options": {
                "England": {"option1": "value1"},
                "France": {"option2": "value2"},
                "Germany": {"option3": "value3"},
                "Italy": {"option4": "value4"},
                "Austria": {"option5": "value5"},
                "Turkey": {"option6": "value6"},
                "Russia": {"option7": "value7"},
            },
        }

        self.service.start(self.game.id)

        self.adjudication_service_mock.start.assert_called_once_with(self.game)

        self.game.refresh_from_db()
        self.assertEqual(self.game.status, models.Game.ACTIVE)
        self.assertEqual(self.game.current_phase.status, models.Phase.ACTIVE)

        # Verify nations are assigned
        nations = [member.nation for member in self.game.members.all()]
        self.assertTrue(all(nations))  # Ensure all members have nations

        # Verify options are assigned to each phase_state
        for member in self.game.members.all():
            phase_state = models.PhaseState.objects.filter(
                phase=self.game.current_phase, member=member
            ).first()
            self.assertIsNotNone(phase_state)
            self.assertEqual(
                phase_state.options,
                json.dumps(
                    self.adjudication_service_mock.start.return_value["options"].get(
                        member.nation
                    )
                ),
            )

        # Verify apply_async is called with correct arguments
        user_ids = [member.user.id for member in self.game.members.all()]
        self.mock_apply_async.assert_called_once_with(
            args=[
                user_ids,
                {
                    "title": "Game Started",
                    "message": f"Game '{self.game.name}' has started!",
                    "game_id": self.game.id,
                    "type": "game_start",
                },
            ],
            kwargs={},
        )

    def test_start_game_adjudication_failure(self):
        # Mock adjudication service to raise an exception
        self.adjudication_service_mock.start.side_effect = Exception(
            "Adjudication failed"
        )

        # Call the start method and assert exception
        with self.assertRaisesMessage(
            exceptions.ValidationError,
            "Adjudication service failed: Adjudication failed",
        ):
            self.service.start(self.game.id)

        # Verify game status remains unchanged
        self.game.refresh_from_db()
        self.assertEqual(self.game.status, models.Game.PENDING)

    def test_start_game_invalid_status(self):
        # Set game status to active
        self.game.status = models.Game.ACTIVE
        self.game.save()

        # Call the start method and assert exception
        with self.assertRaisesMessage(
            exceptions.PermissionDenied, "Cannot start a non-pending game."
        ):
            self.service.start(self.game.id)

        # Verify no interaction with mocks
        self.adjudication_service_mock.start.assert_not_called()
        self.mock_apply_async.assert_not_called()


class TestGameConfirmPhase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)
        self.phase = self.game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
        )
        self.member = self.game.members.first()
        self.phase_state = self.phase.phase_states.create(member=self.member)

    def create_request(self, game_id):
        url = reverse("game-confirm-phase", args=[game_id])
        return self.client.post(url)

    def test_confirm_phase_success(self):
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.phase_state.refresh_from_db()
        self.assertTrue(self.phase_state.orders_confirmed)

    def test_confirm_phase_already_confirmed(self):
        self.phase_state.orders_confirmed = True
        self.phase_state.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.phase_state.refresh_from_db()
        self.assertFalse(self.phase_state.orders_confirmed)

    def test_confirm_phase_game_not_active(self):
        self.game.status = models.Game.PENDING
        self.game.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_user_not_member(self):
        self.member.delete()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_user_eliminated(self):
        self.member.eliminated = True
        self.member.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_user_kicked(self):
        self.member.kicked = True
        self.member.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_unauthenticated(self):
        self.client.logout()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
