from django.urls import reverse
from django.contrib.auth import get_user_model
from game import old_services
from .base import BaseTestCase

User = get_user_model()


class TestGameList(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game1 = old_services.game_create(
            self.user,
            {
                "name": "Game 1",
                "variant": self.variant.id,
            },
        )
        self.game2 = old_services.game_create(
            self.other_user,
            {
                "name": "Game 2",
                "variant": self.variant.id,
            },
        )

    def test_list_all_games(self):
        response = self.client.get(reverse("game-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_list_my_games(self):
        response = self.client.get(reverse("game-list"), {"mine": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Game 1")

    def test_list_games_can_join(self):
        response = self.client.get(reverse("game-list"), {"can_join": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Game 2")

    def test_list_games_with_invalid_filter(self):
        response = self.client.get(reverse("game-list"), {"invalid_filter": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_list_games_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("game-list"))
        self.assertEqual(response.status_code, 401)

    def test_pending_game_user_not_member(self):
        response = self.client.get(reverse("game-list"))
        self.assertEqual(response.status_code, 200)

        game = next((game for game in response.data if game["name"] == "Game 2"), None)

        self.assertIsNotNone(game)
        self.assertIsNotNone(game["id"])
        self.assertEqual(game["name"], "Game 2")
        self.assertEqual(game["status"], "pending")
        self.assertEqual(game["movement_phase_duration"], "24 hours")

        self.assertEqual(game["current_phase"]["season"], "Spring")
        self.assertEqual(game["current_phase"]["year"], "1901")
        self.assertEqual(game["current_phase"]["phase_type"], "Movement")
        self.assertEqual(game["current_phase"]["remaining_time"], None)
        self.assertIsInstance(game["current_phase"]["units"], list)
        self.assertIsInstance(game["current_phase"]["supply_centers"], list)

    def test_list_games_response_structure(self):
        response = self.client.get(reverse("game-list"))
        self.assertEqual(response.status_code, 200)
        for game in response.data:
            self.assertIn("id", game)
            self.assertIn("name", game)
            self.assertIn("status", game)
            self.assertIn("movement_phase_duration", game)
            self.assertIn("can_join", game)
            self.assertIn("can_leave", game)
            self.assertIn("current_phase", game)
            self.assertIn("variant", game)
            self.assertIn("members", game)


class TestGameRetrieve(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = old_services.game_create(
            self.user,
            {
                "name": "Game 1",
                "variant": self.variant.id,
            },
        )

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
