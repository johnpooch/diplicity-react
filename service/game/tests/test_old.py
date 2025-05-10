import json

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch
from rest_framework.test import APITestCase, APIClient
from google.auth.exceptions import GoogleAuthError
from fcm_django.models import FCMDevice
from rest_framework import status

from game.models import (
    Variant,
    Game,
    Member,
    Order,
    Channel,
    ChannelMessage,
    Unit,
    SupplyCenter,
    UserProfile,
)
from game.old_services import (
    game_start,
    game_create,
    adjudication_start,
    adjudication_resolve,
)

User = get_user_model()


class VariantModelTestCase(TestCase):
    def test_variant_creation(self):
        variant = Variant.objects.create(
            id="italy-vs-germany",
            name="Italy vs Germany",
        )
        self.assertEqual(variant.id, "italy-vs-germany")
        self.assertEqual(variant.name, "Italy vs Germany")
        self.assertEqual(
            variant.nations,
            [
                {"name": "Germany", "color": "#90A4AE"},
                {"name": "Italy", "color": "#4CAF50"},
            ],
        )
        self.assertEqual(variant.start["season"], "Spring")
        self.assertEqual(variant.start["year"], 1901)
        self.assertEqual(variant.start["type"], "Movement")
        self.assertIsInstance(variant.start["units"], list)
        self.assertIsInstance(variant.start["supply_centers"], list)


class LoginViewTestCase(APITestCase):

    def setUp(self):
        self.url = reverse("auth-login")

        # Mock Google ID token verification
        self.google_patcher = patch(
            "game.old_services.google_id_token.verify_oauth2_token"
        )
        self.mock_verify_oauth2_token = self.google_patcher.start()
        self.addCleanup(self.google_patcher.stop)
        self.mock_verify_oauth2_token.return_value = {
            "iss": "accounts.google.com",
            "email": "john@doe.com",
            "name": "John Doe",
            "picture": "http://example.com/picture.jpg",
        }

        # Mock token generation
        self.token_patcher = patch("game.old_services.RefreshToken.for_user")
        self.mock_refresh_token = self.token_patcher.start()
        self.addCleanup(self.token_patcher.stop)
        self.mock_refresh_token.return_value = type(
            "MockRefreshToken",
            (object,),
            {
                "access_token": "access_token",
                "__str__": lambda self: "refresh_token",
            },
        )()

        # Add basic return values here

    def create_request(self, data):
        return self.client.post(self.url, data, format="json")

    def test_invalid_request_body_returns_400(self):
        response = self.create_request({})
        self.assertEqual(response.status_code, 400)

    def test_google_auth_verification_error_returns_401(self):
        self.mock_verify_oauth2_token.side_effect = GoogleAuthError(
            "Mocked GoogleAuthError"
        )
        response = self.create_request({"id_token": "token"})
        self.assertEqual(response.status_code, 401)

    def test_google_auth_value_error_returns_401(self):
        self.mock_verify_oauth2_token.side_effect = ValueError("Mocked ValueError")
        response = self.create_request({"id_token": "token"})
        self.assertEqual(response.status_code, 401)

    def test_google_auth_wrong_issuer_returns_401(self):
        self.mock_verify_oauth2_token.return_value = {"iss": "wrong_issuer"}
        response = self.create_request({"id_token": "token"})
        self.assertEqual(response.status_code, 401)

    def test_creates_new_user_if_no_existing_user(self):
        response = self.create_request({"id_token": "token"})
        user_profile = UserProfile.objects.get(user__email="john@doe.com")
        self.assertDictContainsSubset(
            {
                "email": "john@doe.com",
                "username": "johndoe",
                "refresh_token": "refresh_token",
                "access_token": "access_token",
            },
            response.data,
        )
        self.assertEqual(user_profile.picture, "http://example.com/picture.jpg")
        self.assertEqual(user_profile.email, "john@doe.com")
        self.assertEqual(user_profile.name, "John Doe")
        self.assertEqual(user_profile.picture, "http://example.com/picture.jpg")

    def test_existing_user_sign_in(self):
        user = User.objects.create_user(
            email="john@doe.com",
            username="johndoe",
            password="testpassword",
        )
        UserProfile.objects.create(
            user=user,
            name="Old name",
            picture="http://old-website.com/picture.jpg",
        )
        response = self.create_request({"id_token": "token"})
        user_profile = UserProfile.objects.get(user__email="john@doe.com")
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset(
            {
                "email": "john@doe.com",
                "username": "johndoe",
                "refresh_token": "refresh_token",
                "access_token": "access_token",
            },
            response.data,
        )
        self.assertEqual(user_profile.picture, "http://example.com/picture.jpg")
        self.assertEqual(user_profile.name, "John Doe")


class DevicesCreateViewTestCase(APITestCase):

    url = "/devices/"

    def create_request(self, data):
        return self.client.post(self.url, data, format="json")

    def login(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.client.force_authenticate(user=self.user)

    def test_unauthorized_request_returns_401(self):
        response = self.create_request(
            {"registration_id": "test_registration_id", "type": "web"}
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_request_body_returns_400(self):
        self.login()
        response = self.create_request({})
        self.assertEqual(response.status_code, 400)

    def test_valid_request_creates_device(self):
        self.login()
        response = self.create_request(
            {"registration_id": "test_registration_id", "type": "web"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["registration_id"], "test_registration_id")
        self.assertEqual(response.data["type"], "web")

    def test_multiple_requests_with_same_type_creates_multiple_devices(self):
        self.login()
        self.create_request(
            {"registration_id": "test_registration_id_1", "type": "web"}
        )
        self.create_request(
            {"registration_id": "test_registration_id_2", "type": "web"}
        )
        devices = FCMDevice.objects.filter(user=self.user, type="web")
        self.assertEqual(devices[0].active, True)
        self.assertEqual(devices[1].active, True)

    def test_multiple_requests_with_same_registration_id_creates_one_device(self):
        self.login()
        self.create_request({"registration_id": "test_registration_id", "type": "web"})
        self.create_request(
            {"registration_id": "test_registration_id", "type": "android"}
        )
        devices = FCMDevice.objects.filter(user=self.user)
        self.assertEqual(devices.count(), 1)

    def test_device_is_linked_to_user(self):
        self.login()
        self.create_request({"registration_id": "test_registration_id", "type": "web"})
        device = FCMDevice.objects.get(user=self.user)
        self.assertEqual(device.user, self.user)


class GameCreateViewTestCase(APITestCase):

    url = reverse("game-create")
    valid_data = {
        "name": "Test Game",
        "variant": "classical",
    }

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.variant = Variant.objects.create(
            id="classical",
            name="Classical",
        )
        self.client.force_authenticate(user=self.user)

    def create_request(self, data):
        return self.client.post(self.url, data, format="json")

    def test_unauthorized_request_returns_401(self):
        self.client.logout()
        response = self.create_request(self.valid_data)
        self.assertEqual(response.status_code, 401)

    def test_invalid_request_body_returns_400(self):
        response = self.create_request({})
        self.assertEqual(response.status_code, 400)

    def test_variant_does_not_exist_causes_400(self):
        response = self.create_request(
            {
                "name": "Test Game",
                "variant": "non-existent-variant",
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_valid_request_creates_game(self):
        response = self.create_request(self.valid_data)
        self.assertEqual(response.status_code, 201)
        game = Game.objects.get(name="Test Game")
        self.assertEqual(game.name, "Test Game")


# Removed GameLeaveApiTestCase as it has been moved to test_game.py


# class OrderCreateApiTestCase(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         variant = Variant.objects.create(
#             id="test-variant",
#             name="Test Variant",
#         )
#         self.user = User.objects.create_user(username="testuser", password="password")
#         self.game = Game.objects.create(
#             name="Test Game",
#             variant=variant,
#             status=Game.ACTIVE,
#         )
#         self.member = self.game.members.create(user=self.user)
#         self.phase = self.game.phases.create(
#             game=self.game,
#             season="Spring",
#             year=1901,
#             type="Movement",
#         )

#         phase_state = self.phase.phase_states.create(member=self.member)
#         with open("/app/service/game/data/options/options.json") as f:
#             json_string = f.read()
#         phase_state.options = json.loads(json_string)
#         phase_state.save()
#         self.client.force_authenticate(user=self.user)

#     def create_request(self, game_id, data):
#         url = reverse("order-create", args=[game_id])
#         return self.client.post(url, data, format="json")

#     def test_create_hold_valid(self):
#         data = {
#             "source": "bud",
#             "order_type": "Hold",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)

#     def test_create_hold_invalid(self):
#         data = {
#             "source": "invalid_source",
#             "order_type": "Hold",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_create_move_valid(self):
#         data = {
#             "source": "bud",
#             "target": "tri",
#             "order_type": "Move",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)

#     def test_create_move_invalid(self):
#         data = {
#             "source": "bud",
#             "target": "invalid_target",
#             "order_type": "Move",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_create_support_valid(self):
#         data = {
#             "source": "bud",
#             "aux": "sev",
#             "target": "rum",
#             "order_type": "Support",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)

#     def test_create_support_invalid(self):
#         data = {
#             "source": "bud",
#             "aux": "invalid_aux",
#             "target": "rum",
#             "order_type": "Support",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_create_order_invalid_order_type(self):
#         data = {
#             "source": "bud",
#             "target": "tri",
#             "order_type": "InvalidOrderType",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_create_order_game_not_found(self):
#         data = {
#             "source": "bud",
#             "order_type": "Hold",
#         }
#         response = self.create_request(999, data)
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

#     def test_create_order_user_not_a_member(self):
#         self.member.delete()  # Remove the user as a member
#         data = {
#             "source": "bud",
#             "order_type": "Hold",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

#     def test_create_order_game_not_active(self):
#         self.game.status = Game.PENDING
#         self.game.save()
#         data = {
#             "source": "bud",
#             "order_type": "Hold",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_create_order_unauthorized(self):
#         self.client.logout()
#         data = {
#             "source": "bud",
#             "order_type": "Hold",
#         }
#         response = self.create_request(self.game.id, data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# class AdjudicationServiceTestCase(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username="testuser", password="password")
#         self.variant = Variant.objects.create(
#             id="classical",
#             name="Classical",
#         )
#         self.game = Game.objects.create(
#             name="Test Game",
#             variant=self.variant,
#             status=Game.ACTIVE,
#         )

#     @patch("requests.get")
#     def test_start_with_classical_data(self, mock_get):
#         with open("/app/service/game/data/starts/classical.json") as f:
#             mock_response_data = f.read()

#         mock_get.return_value.status_code = 200
#         mock_get.return_value.json.return_value = mock_response_data

#         response = adjudication_start(self.game.id)

#         self.assertIn("phase", response)
#         self.assertIn("options", response)
#         self.assertEqual(response["phase"]["season"], "Spring")
#         self.assertEqual(response["phase"]["year"], 1901)
#         self.assertEqual(response["phase"]["type"], "Movement")
#         self.assertIn("units", response["phase"])
#         self.assertIn("orders", response["phase"])
#         self.assertIn("supply_centers", response["phase"])

#     def test_resolve(self):
#         self.phase = self.game.phases.create(
#             game=self.game,
#             season="Spring",
#             year=1901,
#             type="Movement",
#         )

#         self.phase.units.create(
#             type="Fleet",
#             nation="England",
#             province="lon",
#         )

#         self.member = self.game.members.create(user=self.user, nation="England")
#         self.phase_state = self.phase.phase_states.create(member=self.member)
#         self.order = Order.objects.create(
#             phase_state=self.phase_state,
#             order_type="Move",
#             source="lon",
#             target="eng",
#         )

#         response = adjudication_resolve(self.game.id)

#         self.assertIn("phase", response)
#         self.assertIn("options", response)
#         self.assertEqual(response["phase"]["season"], "Spring")
#         self.assertEqual(response["phase"]["year"], 1901)
#         self.assertEqual(response["phase"]["type"], "Retreat")
#         self.assertIn("units", response["phase"])
#         self.assertIn("orders", response["phase"])
#         self.assertIn("supply_centers", response["phase"])
#         self.assertEqual(response["phase"]["resolutions"]["lon"], "OK")


class PhaseStateConfirmApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        variant = Variant.objects.create(
            id="test-variant",
            name="Test Variant",
        )
        self.user = User.objects.create_user(username="testuser", password="password")
        self.game = Game.objects.create(
            name="Test Game",
            variant=variant,
            status=Game.ACTIVE,
        )
        self.member = self.game.members.create(user=self.user)
        self.phase = self.game.phases.create(
            game=self.game,
            season="Spring",
            year=1901,
            type="Movement",
        )
        self.phase_state = self.phase.phase_states.create(member=self.member)
        self.client.force_authenticate(user=self.user)

    def create_request(self, game_id):
        url = reverse("phase-state-confirm", args=[game_id])
        return self.client.post(url)

    def test_confirm_phase_state_success(self):
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.phase_state.refresh_from_db()
        self.assertTrue(self.phase_state.orders_confirmed)

    def test_confirm_phase_state_already_confirmed(self):
        self.phase_state.orders_confirmed = True
        self.phase_state.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_confirm_phase_state_game_not_active(self):
        self.game.status = Game.PENDING
        self.game.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_state_user_not_member(self):
        self.member.delete()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_state_user_eliminated(self):
        self.member.eliminated = True
        self.member.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_state_user_kicked(self):
        self.member.kicked = True
        self.member.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_phase_state_unauthorized(self):
        self.client.logout()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VariantListApiTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.variant = Variant.objects.create(
            id="classical",
            name="Classical",
        )
        self.client.force_authenticate(user=self.user)

    def test_list_variants_success(self):
        response = self.client.get(reverse("variant-list"))
        classical = next(
            (variant for variant in response.data if variant["id"] == "classical"), None
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(classical["id"], "classical")
        self.assertEqual(classical["name"], "Classical")
        self.assertEqual(classical["description"], "The original game of Diplomacy")
        self.assertEqual(classical["author"], "Allan B. Calhamer")

        self.assertEqual(len(classical["nations"]), 7)
        self.assertEqual(classical["nations"][0]["name"], "England")
        self.assertEqual(classical["nations"][0]["color"], "#2196F3")

        self.assertEqual(classical["start"]["season"], "Spring")
        self.assertEqual(classical["start"]["year"], "1901")
        self.assertEqual(classical["start"]["type"], "Movement")

        self.assertIsInstance(classical["start"]["units"], list)
        self.assertIsInstance(classical["start"]["supply_centers"], list)

        self.assertEqual(
            classical["start"]["units"][0],
            {
                "type": "Fleet",
                "nation": "England",
                "province": "edi",
            },
        )
        self.assertEqual(
            classical["start"]["supply_centers"][0],
            {
                "nation": "England",
                "province": "edi",
            },
        )

    def test_list_variants_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("variant-list"))
        self.assertEqual(response.status_code, 401)


class GameRetrieveApiTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.variant = Variant.objects.create(
            id="classical",
            name="Classical",
        )

        self.game = game_create(
            self.user,
            {
                "name": "Game 1",
                "variant": self.variant.id,
            },
        )

    def create_request(self, game_id):
        url = reverse("game-retrieve", args=[game_id])
        return self.client.get(url)

    def test_retrieve_game_success(self):
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.game.id)
        self.assertEqual(response.data["name"], self.game.name)

    def test_retrieve_game_not_found(self):
        response = self.create_request(999)
        self.assertEqual(response.status_code, 404)

    def test_retrieve_game_unauthenticated(self):
        self.client.logout()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, 401)


class ChannelCreateApiTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.variant = Variant.objects.create(
            id="classical",
            name="Classical",
        )

        self.game = game_create(
            self.user,
            {
                "name": "Test Game",
                "variant": self.variant.id,
            },
        )
        self.game.status = Game.ACTIVE
        self.game.save()

        self.member1 = self.game.members.get(user=self.user)
        self.member1.nation = "England"
        self.member1.save()
        self.member2 = self.game.members.create(user=self.other_user, nation="France")

    def create_request(self, game_id, data):
        url = reverse("channel-create", args=[game_id])
        return self.client.post(url, data, format="json")

    def test_create_channel_success(self):
        data = {"members": [self.member2.id]}  # Exclude the logged-in user
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Channel.objects.count(), 1)
        channel = Channel.objects.first()
        self.assertEqual(channel.name, "England, France")  # Includes logged-in user
        self.assertTrue(channel.private)

    def test_create_channel_empty_members(self):
        data = {"members": []}
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Members list cannot be empty.", str(response.data))

    def test_create_channel_duplicate_members(self):
        Channel.objects.create(
            name="England, France", private=True, game=self.game
        ).members.set([self.member1, self.member2])
        data = {"members": [self.member2.id]}  # Exclude the logged-in user
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, 400)

    def test_create_channel_invalid_member(self):
        other_game = Game.objects.create(
            name="Other Game",
            variant=self.variant,
            status=Game.ACTIVE,
        )
        invalid_member = Member.objects.create(user=self.other_user, game=other_game)
        data = {"members": [invalid_member.id]}
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, 400)

    def test_create_channel_unauthenticated(self):
        self.client.logout()
        data = {"members": [self.member1.id, self.member2.id]}
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, 401)


class ChannelMessageCreateApiTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.variant = Variant.objects.create(
            id="classical",
            name="Classical",
        )

        self.game = game_create(
            self.user,
            {
                "name": "Test Game",
                "variant": self.variant.id,
            },
        )
        self.game.status = Game.ACTIVE
        self.game.save()

        self.member1 = self.game.members.get(user=self.user)
        self.member2 = self.game.members.create(user=self.other_user, nation="France")

        self.channel = Channel.objects.create(
            name="Test Channel", private=True, game=self.game
        )
        self.channel.members.set([self.member1, self.member2])

    def create_request(self, game_id, channel_id, data):
        url = reverse("channel-message-create", args=[game_id, channel_id])
        return self.client.post(url, data, format="json")

    def test_create_message_success(self):
        data = {"body": "Hello, this is a test message."}
        response = self.create_request(self.game.id, self.channel.id, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ChannelMessage.objects.count(), 1)
        message = ChannelMessage.objects.first()
        self.assertEqual(message.body, data["body"])
        self.assertEqual(message.sender, self.member1)

    def test_create_message_empty_body(self):
        data = {"body": ""}
        response = self.create_request(self.game.id, self.channel.id, data)
        self.assertEqual(response.status_code, 400)

    def test_create_message_exceeds_length(self):
        data = {"body": "a" * 1001}  # Exceeds the 1000 character limit
        response = self.create_request(self.game.id, self.channel.id, data)
        self.assertEqual(response.status_code, 400)

    def test_create_message_user_not_in_channel(self):
        self.channel.members.remove(self.member1)
        data = {"body": "Hello, this is a test message."}
        response = self.create_request(self.game.id, self.channel.id, data)
        self.assertEqual(response.status_code, 403)
        self.assertIn("User is not a member of the channel.", str(response.data))

    def test_create_message_game_not_active(self):
        self.game.status = Game.PENDING
        self.game.save()
        data = {"body": "Hello, this is a test message."}
        response = self.create_request(self.game.id, self.channel.id, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Game is not active.", str(response.data))

    def test_create_message_channel_not_found(self):
        data = {"body": "Hello, this is a test message."}
        response = self.create_request(self.game.id, 999, data)
        self.assertEqual(response.status_code, 404)

    def test_create_message_game_not_found(self):
        data = {"body": "Hello, this is a test message."}
        response = self.create_request(999, self.channel.id, data)
        self.assertEqual(response.status_code, 404)

    def test_create_message_unauthenticated(self):
        self.client.logout()
        data = {"body": "Hello, this is a test message."}
        response = self.create_request(self.game.id, self.channel.id, data)
        self.assertEqual(response.status_code, 401)

    @patch("game.old_services.notification_create")
    def test_create_message_sends_notification(self, mock_notification_create):
        data = {"body": "Hello, this is a test message."}
        response = self.create_request(self.game.id, self.channel.id, data)
        self.assertEqual(response.status_code, 201)

        # Assert notification is sent to other members
        mock_notification_create.assert_called_once()
        notification_args = mock_notification_create.call_args[0]
        self.assertIn(self.member2.user.id, notification_args[0])  # Other member
        self.assertNotIn(self.member1.user.id, notification_args[0])  # Sender excluded
        self.assertEqual(notification_args[1]["title"], "New Message")
        self.assertEqual(
            notification_args[1]["body"],
            f"{self.member1.user.username} sent a message in {self.channel.name}.",
        )
        self.assertEqual(notification_args[1]["game_id"], str(self.game.id))
        self.assertEqual(notification_args[1]["channel_id"], str(self.channel.id))


class ChannelListApiTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.variant = Variant.objects.create(
            id="classical",
            name="Classical",
        )
        self.game = game_create(
            self.user,
            {
                "name": "Test Game",
                "variant": self.variant.id,
            },
        )
        self.game.status = Game.ACTIVE
        self.game.save()

        self.member1 = self.game.members.get(user=self.user)
        self.member2 = self.game.members.create(user=self.other_user, nation="France")

        self.public_channel = Channel.objects.create(
            name="Public Channel", private=False, game=self.game
        )
        self.private_channel = Channel.objects.create(
            name="Private Channel", private=True, game=self.game
        )
        self.private_channel.members.set([self.member1])

    def create_request(self, game_id):
        url = reverse("channel-list", args=[game_id])
        return self.client.get(url)

    def test_list_channels_success(self):
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # Public + private channel user is in

        public_channel = next(
            (
                channel
                for channel in response.data
                if channel["name"] == "Public Channel"
            ),
            None,
        )
        self.assertIsNotNone(public_channel)
        self.assertEqual(public_channel["private"], False)

        private_channel = next(
            (
                channel
                for channel in response.data
                if channel["name"] == "Private Channel"
            ),
            None,
        )
        self.assertIsNotNone(private_channel)
        self.assertEqual(private_channel["private"], True)

    def test_list_channels_excludes_private_channels_user_not_in(self):
        self.private_channel.members.remove(self.member1)
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)  # Only public channel

    def test_list_channels_includes_messages(self):
        ChannelMessage.objects.create(
            channel=self.public_channel,
            sender=self.member1,
            body="Test message",
        )
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, 200)

        public_channel = next(
            (
                channel
                for channel in response.data
                if channel["name"] == "Public Channel"
            ),
            None,
        )
        self.assertIsNotNone(public_channel)
        self.assertEqual(len(public_channel["messages"]), 1)
        self.assertEqual(public_channel["messages"][0]["body"], "Test message")

    def test_list_channels_unauthenticated(self):
        self.client.logout()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, 401)


class UserProfileRetrieveViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.profile = UserProfile.objects.create(
            user=self.user, name="Test User", picture="http://example.com/picture.jpg"
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_profile_success(self):
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Test User")
        self.assertEqual(response.data["picture"], "http://example.com/picture.jpg")
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)

    def test_retrieve_user_profile_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(response.status_code, 401)


# from django.utils import timezone
# from datetime import timedelta

# class GameStartApiTestCase(APITestCase):
#     def setUp(self):
#         # ...existing code...

#     @patch("game.services.game_resolve.apply_async")
#     def test_game_start_creates_resolution_task(self, mock_apply_async):
#         # Start game setup code...
#         game_start(self.game.id)

#         self.game.refresh_from_db()
#         self.assertIsNotNone(self.game.resolution_task)
#         self.assertEqual(self.game.resolution_task.status, Task.PENDING)

#         # Check scheduled time is ~24 hours from now
#         expected_time = timezone.now() + timedelta(hours=24)
#         self.assertAlmostEqual(
#             self.game.resolution_task.scheduled_for.timestamp(),
#             expected_time.timestamp(),
#             delta=5
#         )

#         # Verify task was scheduled
#         mock_apply_async.assert_called_once_with(
#             args=[self.game.id],
#             countdown=24 * 60 * 60,
#             task_id=self.game.resolution_task.id
#         )

# class GameResolveTaskTestCase(APITestCase):
#     def setUp(self):
#         # ... Similar setup to other game tests ...

#     @patch("game.services.adjudication_resolve")
#     @patch("game.services.game_resolve.apply_async")
#     def test_resolution_creates_new_task(self, mock_apply_async, mock_adjudicate):
#         mock_adjudicate.return_value = {
#             "phase": {
#                 "season": "Spring",
#                 "year": 1901,
#                 "type": "Movement",
#                 "units": [],
#                 "orders": {},
#                 "supply_centers": [],
#                 "dislodgeds": {},
#                 "dislodgers": {},
#                 "bounces": {},
#                 "resolutions": {},
#             },
#             "options": {"England": {}, "France": {}},
#         }

#         old_task = self.game.resolution_task
#         game_resolve(self.game.id)

#         self.game.refresh_from_db()
#         self.assertNotEqual(self.game.resolution_task.id, old_task.id)
#         self.assertEqual(old_task.status, Task.COMPLETED)

#         # Verify new task was scheduled
#         mock_apply_async.assert_called_once_with(
#             args=[self.game.id],
#             countdown=24 * 60 * 60,
#             task_id=self.game.resolution_task.id
#         )
