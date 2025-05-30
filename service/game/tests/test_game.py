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
        member = next(
            member
            for member in game["members"]
            if member["username"] == self.user.username
        )

        self.assertEqual(game["id"], self.game1.id)
        self.assertEqual(game["name"], "Game 1")
        self.assertEqual(game["status"], "pending")
        self.assertEqual(game["movement_phase_duration"], "24 hours")
        self.assertEqual(game["nation_assignment"], models.Game.RANDOM)
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

        self.assertEqual(member["username"], self.user.username)
        self.assertEqual(member["name"], self.user.profile.name)
        self.assertEqual(member["picture"], self.user.profile.picture)
        self.assertEqual(member["nation"], "England")
        self.assertEqual(member["is_current_user"], True)

        # Test list endpoint with ordered nation assignment
        self.game1.nation_assignment = models.Game.ORDERED
        self.game1.save()
        response = self.create_request()
        game = next(game for game in response.data if game["name"] == "Game 1")
        self.assertEqual(game["nation_assignment"], models.Game.ORDERED)

        # Test retrieve endpoint
        response = self.client.get(reverse("game-retrieve", args=[self.game1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nation_assignment"], models.Game.ORDERED)


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
        self.assertIn("nation_assignment", response.data)
        self.assertEqual(
            response.data["nation_assignment"], models.Game.RANDOM
        )  # Default value
        self.assertIn("can_join", response.data)
        self.assertIn("can_leave", response.data)
        self.assertIn("current_phase", response.data)
        self.assertIn("variant", response.data)
        self.assertIn("members", response.data)

        # Test with ordered nation assignment
        self.game.nation_assignment = models.Game.ORDERED
        self.game.save()
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["nation_assignment"], models.Game.ORDERED)


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

        # Verify default nation assignment is random
        game = models.Game.objects.get(id=response.data["id"])
        self.assertEqual(game.nation_assignment, models.Game.RANDOM)

        # Verify public channel was created
        channel = models.Channel.objects.filter(game=game).first()
        self.assertIsNotNone(channel)
        self.assertEqual(channel.name, "Public Press")
        self.assertFalse(channel.private)

    def test_create_game_with_ordered_nation_assignment(self):
        payload = {
            "name": "New Game",
            "variant": self.variant.id,
            "nation_assignment": models.Game.ORDERED,
        }
        response = self.create_request(payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        game = models.Game.objects.get(id=response.data["id"])
        self.assertEqual(game.nation_assignment, models.Game.ORDERED)

        # Verify public channel was created
        channel = models.Channel.objects.filter(game=game).first()
        self.assertIsNotNone(channel)
        self.assertEqual(channel.name, "Public Press")
        self.assertFalse(channel.private)

    def test_create_game_public_channel_unique(self):
        """Test that each game gets its own unique public channel"""
        # Create first game
        payload1 = {"name": "Game 1", "variant": self.variant.id}
        response1 = self.create_request(payload1)
        game1 = models.Game.objects.get(id=response1.data["id"])
        channel1 = models.Channel.objects.get(game=game1)

        # Create second game
        payload2 = {"name": "Game 2", "variant": self.variant.id}
        response2 = self.create_request(payload2)
        game2 = models.Game.objects.get(id=response2.data["id"])
        channel2 = models.Channel.objects.get(game=game2)

        # Verify each game has its own channel
        self.assertNotEqual(channel1.id, channel2.id)
        self.assertEqual(channel1.name, "Public Press")
        self.assertEqual(channel2.name, "Public Press")
        self.assertFalse(channel1.private)
        self.assertFalse(channel2.private)

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

        self.notify_apply_async_patch = patch("game.tasks.notify_task.apply_async")
        self.mock_notify_apply_async = self.notify_apply_async_patch.start()

        self.resolve_apply_async_patch = patch("game.tasks.resolve_task.apply_async")
        self.mock_resolve_apply_async = self.resolve_apply_async_patch.start()

        mock_task_result = MagicMock(task_id=12345)

        self.mock_resolve_apply_async.return_value = mock_task_result

        models.Task.objects.create(id=mock_task_result.task_id)

        self.addCleanup(self.notify_apply_async_patch.stop)
        self.addCleanup(self.resolve_apply_async_patch.stop)

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
        self.mock_notify_apply_async.assert_called_once_with(
            args=[
                user_ids,
                {
                    "title": "Game Started",
                    "body": f"Game '{self.game.name}' has started!",
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
        self.mock_notify_apply_async.assert_not_called()
        self.mock_resolve_apply_async.assert_not_called()


class TestGameConfirmPhase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)
        self.phase = self.game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
            status=models.Phase.ACTIVE,
        )
        self.member = self.game.members.first()
        self.phase_state = self.phase.phase_states.create(member=self.member)
        # Add mock for adjudication service
        self.adjudication_service_mock = MagicMock()
        self.service = GameService(
            user=self.user,
            adjudication_service=self.adjudication_service_mock,
        )
        # Add patches for tasks
        self.resolve_task_patch = patch("game.tasks.resolve_task.apply_async")
        self.mock_resolve_task = self.resolve_task_patch.start()
        self.addCleanup(self.resolve_task_patch.stop)

    def test_confirm_phase_success(self):
        response = self.client.post(reverse("game-confirm-phase", args=[self.game.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.phase_state.refresh_from_db()
        self.assertTrue(self.phase_state.orders_confirmed)

    def test_confirm_phase_already_confirmed(self):
        self.phase_state.orders_confirmed = True
        self.phase_state.save()
        response = self.client.post(reverse("game-confirm-phase", args=[self.game.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.phase_state.refresh_from_db()
        self.assertFalse(self.phase_state.orders_confirmed)

    def test_confirm_phase_game_not_active(self):
        self.game.status = models.Game.PENDING
        self.game.save()
        response = self.client.post(reverse("game-confirm-phase", args=[self.game.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_user_not_member(self):
        self.member.delete()
        response = self.client.post(reverse("game-confirm-phase", args=[self.game.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_user_eliminated(self):
        self.member.eliminated = True
        self.member.save()
        response = self.client.post(reverse("game-confirm-phase", args=[self.game.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_user_kicked(self):
        self.member.kicked = True
        self.member.save()
        response = self.client.post(reverse("game-confirm-phase", args=[self.game.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_unauthenticated(self):
        self.client.logout()
        response = self.client.post(reverse("game-confirm-phase", args=[self.game.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_confirm_phase_auto_resolve_single_player(self):
        """Test that phase is auto-resolved when the only active player confirms orders"""
        # Create a resolution task
        task = models.Task.objects.create()
        self.game.resolution_task = task
        self.game.save()

        # Confirm orders
        self.service.confirm_phase(self.game.id)

        # Verify task was executed immediately
        self.mock_resolve_task.assert_called_once_with(
            args=[self.game.id], kwargs={}, task_id=task.id, countdown=0
        )

    def test_confirm_phase_no_auto_resolve_eliminated_player(self):
        """Test that eliminated player's confirmation doesn't trigger auto-resolve"""
        # Create another member who is eliminated
        other_member = self.game.members.create(user=self.other_user, eliminated=True)
        other_phase_state = self.phase.phase_states.create(member=other_member)

        # Create a resolution task
        task = models.Task.objects.create()
        self.game.resolution_task = task
        self.game.save()

        # Eliminated player confirms
        self.service.user = self.other_user
        other_phase_state.orders_confirmed = True
        other_phase_state.save()

        # Active player confirms
        self.service.user = self.user
        self.service.confirm_phase(self.game.id)

        # Verify task was executed immediately (only active player matters)
        self.mock_resolve_task.assert_called_once_with(
            args=[self.game.id], kwargs={}, task_id=task.id, countdown=0
        )

    def test_confirm_phase_no_auto_resolve_kicked_player(self):
        """Test that kicked player's confirmation doesn't trigger auto-resolve"""
        # Create another member who is kicked
        other_member = self.game.members.create(user=self.other_user, kicked=True)
        other_phase_state = self.phase.phase_states.create(member=other_member)

        # Create a resolution task
        task = models.Task.objects.create()
        self.game.resolution_task = task
        self.game.save()

        # Kicked player confirms
        self.service.user = self.other_user
        other_phase_state.orders_confirmed = True
        other_phase_state.save()

        # Active player confirms
        self.service.user = self.user
        self.service.confirm_phase(self.game.id)

        # Verify task was executed immediately (only active player matters)
        self.mock_resolve_task.assert_called_once_with(
            args=[self.game.id], kwargs={}, task_id=task.id, countdown=0
        )

    def test_confirm_phase_no_resolution_task(self):
        """Test that no error occurs when there's no resolution task"""
        # Confirm orders without a resolution task
        self.service.confirm_phase(self.game.id)

        # Verify no task execution was attempted
        self.mock_resolve_task.assert_not_called()

    def test_unconfirm_phase_no_auto_resolve(self):
        """Test that unconfirming orders doesn't trigger auto-resolve"""
        # Create a resolution task
        task = models.Task.objects.create()
        self.game.resolution_task = task
        self.game.save()

        # First confirm the orders
        self.phase_state.orders_confirmed = True
        self.phase_state.save()

        # Then unconfirm
        self.service.confirm_phase(self.game.id)

        # Verify task was not executed
        self.mock_resolve_task.assert_not_called()


class TestGamePhaseProperties(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)
        self.phase = self.game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
            status=models.Phase.ACTIVE,
        )
        self.member = self.game.members.first()
        self.phase_state = self.phase.phase_states.create(member=self.member)

    def test_phase_confirmed_true(self):
        self.phase_state.orders_confirmed = True
        self.phase_state.save()
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["phase_confirmed"])

    def test_phase_confirmed_false(self):
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["phase_confirmed"])

    def test_phase_confirmed_inactive_phase(self):
        # Change phase to inactive and confirm it doesn't show as confirmed
        self.phase.status = models.Phase.COMPLETED
        self.phase.save()
        self.phase_state.orders_confirmed = True
        self.phase_state.save()
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["phase_confirmed"])

    def test_phase_confirmed_other_user(self):
        # Create a new member for other_user
        self.game.members.create(user=self.other_user)
        # Switch authentication to other user
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["phase_confirmed"])

    def test_can_confirm_phase_true(self):
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["can_confirm_phase"])

    def test_can_confirm_phase_false_eliminated(self):
        self.member.eliminated = True
        self.member.save()
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["can_confirm_phase"])

    def test_can_confirm_phase_false_kicked(self):
        self.member.kicked = True
        self.member.save()
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["can_confirm_phase"])

    def test_can_confirm_phase_false_inactive_phase(self):
        self.phase.status = models.Phase.COMPLETED
        self.phase.save()
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["can_confirm_phase"])

    def test_can_confirm_phase_false_non_member(self):
        # Login as a user who is not a member of the game
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse("game-retrieve", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["can_confirm_phase"])

    def test_game_without_phases(self):
        # Test edge case where a game doesn't have any phases
        game_without_phases = self.create_game(
            self.user, "No Phases Game", status=models.Game.PENDING
        )
        response = self.client.get(
            reverse("game-retrieve", args=[game_without_phases.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["phase_confirmed"])
        self.assertFalse(
            response.data["can_confirm_phase"]
        )  # Can't confirm when no active phase


class TestGameResolve(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Test Game", status=models.Game.ACTIVE)
        self.phase = self.game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
            status=models.Phase.ACTIVE,
        )
        self.member = self.game.members.first()
        self.member.nation = "England"
        self.member.save()
        self.phase_state = self.phase.phase_states.create(member=self.member)
        self.adjudication_service_mock = MagicMock()

        self.notify_apply_async_patch = patch("game.tasks.notify_task.apply_async")
        self.mock_notify_apply_async = self.notify_apply_async_patch.start()

        self.resolve_apply_async_patch = patch("game.tasks.resolve_task.apply_async")
        self.mock_resolve_apply_async = self.resolve_apply_async_patch.start()

        mock_task_result = MagicMock(task_id=12345)

        self.mock_resolve_apply_async.return_value = mock_task_result

        models.Task.objects.create(id=mock_task_result.task_id)

        self.addCleanup(self.notify_apply_async_patch.stop)
        self.addCleanup(self.resolve_apply_async_patch.stop)

        self.service = GameService(
            user=self.user,
            adjudication_service=self.adjudication_service_mock,
        )

    def test_resolve_successful_move(self):
        # Create an order
        order = self.phase_state.orders.create(
            order_type="Move", source="lon", target="eng"
        )

        # Mock adjudication service response
        self.adjudication_service_mock.resolve.return_value = {
            "phase": {
                "season": "Spring",
                "year": 1901,
                "type": "Retreat",
                "resolutions": [{"province": "lon", "result": "OK", "by": None}],
                "units": [
                    {
                        "type": "Fleet",
                        "nation": "England",
                        "province": "London",
                        "dislodged": False,
                        "dislodged_by": None,
                    }
                ],
                "supply_centers": [{"province": "London", "nation": "England"}],
            },
            "options": {"England": {"option1": "value1"}},
        }

        self.service.resolve(self.game.id)

        # Verify resolution was created
        resolution = models.OrderResolution.objects.get(order=order)
        self.assertEqual(resolution.status, "OK")
        self.assertIsNone(resolution.by)

    def test_resolve_bounce(self):
        # Create an order
        order = self.phase_state.orders.create(
            order_type="Move", source="lon", target="wal"
        )

        # Mock adjudication service response
        self.adjudication_service_mock.resolve.return_value = {
            "phase": {
                "season": "Spring",
                "year": 1901,
                "type": "Retreat",
                "resolutions": [
                    {"province": "lon", "result": "ErrBounce", "by": "lvp"}
                ],
                "units": [
                    {
                        "type": "Fleet",
                        "nation": "England",
                        "province": "London",
                        "dislodged": False,
                        "dislodged_by": None,
                    }
                ],
                "supply_centers": [{"province": "London", "nation": "England"}],
            },
            "options": {"England": {"option1": "value1"}},
        }

        self.service.resolve(self.game.id)

        # Verify resolution was created
        resolution = models.OrderResolution.objects.get(order=order)
        self.assertEqual(resolution.status, "ErrBounce")
        self.assertEqual(resolution.by, "lvp")

    def test_resolve_invalid_support_order(self):
        # Create an order
        order = self.phase_state.orders.create(
            order_type="Support", source="lon", target="wal", aux="eng"
        )

        # Mock adjudication service response
        self.adjudication_service_mock.resolve.return_value = {
            "phase": {
                "season": "Spring",
                "year": 1901,
                "type": "Retreat",
                "resolutions": [
                    {
                        "province": "lon",
                        "result": "ErrInvalidSupporteeOrder",
                        "by": None,
                    }
                ],
                "units": [
                    {
                        "type": "Fleet",
                        "nation": "England",
                        "province": "London",
                        "dislodged": False,
                        "dislodged_by": None,
                    }
                ],
                "supply_centers": [{"province": "London", "nation": "England"}],
            },
            "options": {"England": {"option1": "value1"}},
        }

        self.service.resolve(self.game.id)

        # Verify resolution was created
        resolution = models.OrderResolution.objects.get(order=order)
        self.assertEqual(resolution.status, "ErrInvalidSupporteeOrder")
        self.assertIsNone(resolution.by)

    def test_resolve_multiple_orders(self):
        # Create orders
        order1 = self.phase_state.orders.create(
            order_type="Move", source="lon", target="eng"
        )
        order2 = self.phase_state.orders.create(
            order_type="Support", source="lvp", target="lon", aux="eng"
        )

        # Mock adjudication service response
        self.adjudication_service_mock.resolve.return_value = {
            "phase": {
                "season": "Spring",
                "year": 1901,
                "type": "Retreat",
                "resolutions": [
                    {"province": "lon", "result": "OK", "by": None},
                    {"province": "lvp", "result": "OK", "by": None},
                ],
                "units": [
                    {
                        "type": "Fleet",
                        "nation": "England",
                        "province": "London",
                        "dislodged": False,
                        "dislodged_by": None,
                    },
                ],
                "supply_centers": [{"province": "London", "nation": "England"}],
            },
            "options": {"England": {"option1": "value1"}},
        }

        self.service.resolve(self.game.id)

        # Verify resolutions were created
        resolution1 = models.OrderResolution.objects.get(order=order1)
        self.assertEqual(resolution1.status, "OK")
        self.assertIsNone(resolution1.by)

        resolution2 = models.OrderResolution.objects.get(order=order2)
        self.assertEqual(resolution2.status, "OK")
        self.assertIsNone(resolution2.by)

    def test_resolve_adjudication_failure(self):
        # Mock adjudication service to raise an exception
        self.adjudication_service_mock.resolve.side_effect = Exception(
            "Adjudication failed"
        )

        # Create an order
        self.phase_state.orders.create(order_type="Move", source="lon", target="eng")

        # Call the resolve method and assert exception
        with self.assertRaisesMessage(
            exceptions.ValidationError,
            "Adjudication service failed: Adjudication failed",
        ):
            self.service.resolve(self.game.id)

        # Verify no resolutions were created
        self.assertEqual(models.OrderResolution.objects.count(), 0)
