import json
from django.urls import reverse
from rest_framework import status
from .base import BaseTestCase
from game import models


class TestOrderCreate(BaseTestCase):
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
        with open("/app/service/game/data/options/options.json") as f:
            json_string = f.read()
        self.phase_state.options = json.dumps(json.loads(json_string))
        self.phase_state.save()

    def create_request(self, game_id, payload):
        url = reverse("order-create", args=[game_id])
        return self.client.post(url, payload, content_type="application/json")

    def test_create_hold_valid(self):
        data = {
            "source": "bud",
            "order_type": "Hold",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_hold_invalid(self):
        data = {
            "source": "invalid_source",
            "order_type": "Hold",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_move_valid(self):
        data = {
            "source": "bud",
            "target": "tri",
            "order_type": "Move",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_move_invalid(self):
        data = {
            "source": "bud",
            "target": "invalid_target",
            "order_type": "Move",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_support_valid(self):
        data = {
            "source": "bud",
            "aux": "sev",
            "target": "rum",
            "order_type": "Support",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_support_invalid(self):
        data = {
            "source": "bud",
            "aux": "invalid_aux",
            "target": "rum",
            "order_type": "Support",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_invalid_order_type(self):
        data = {
            "source": "bud",
            "target": "tri",
            "order_type": "InvalidOrderType",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_game_not_found(self):
        data = {
            "source": "bud",
            "order_type": "Hold",
        }
        response = self.create_request(999, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_order_user_not_a_member(self):
        self.member.delete()  # Remove the user as a member
        data = {
            "source": "bud",
            "order_type": "Hold",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_game_not_active(self):
        self.game.status = models.Game.PENDING
        self.game.save()
        data = {
            "source": "bud",
            "order_type": "Hold",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_unauthorized(self):
        self.client.logout()
        data = {
            "source": "bud",
            "order_type": "Hold",
        }
        response = self.create_request(self.game.id, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestOrderList(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)
        self.phase = self.game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
        )
        self.member = self.game.members.first()

        # Create another member
        self.other_user = self.create_user("other_user", "password")
        self.other_member = self.game.members.create(
            user=self.other_user, nation="France"
        )
        self.member.nation = "Austria"
        self.member.save()

        # Create phase states
        self.phase_state_user = self.phase.phase_states.create(member=self.member)
        self.phase_state_other = self.phase.phase_states.create(
            member=self.other_member
        )

        # Add orders to the user's phase state
        self.phase_state_user.orders.create(order_type="Hold", source="bud")
        self.phase_state_user.orders.create(
            order_type="Move", source="bud", target="tri"
        )

        # Add orders to the other member's phase state
        self.phase_state_other.orders.create(
            order_type="Support", source="par", target="mar", aux="bur"
        )
        self.phase_state_other.orders.create(
            order_type="Convoy", source="bre", target="lon", aux="eng"
        )

    def create_request(self, game_id, phase_id):
        url = reverse("order-list", args=[game_id, phase_id])
        return self.client.get(url, content_type="application/json")

    def test_list_orders_active_phase(self):
        response = self.create_request(self.game.id, self.phase.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert the response contains orders for the user's nation only
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nation"], self.member.nation)
        self.assertEqual(len(response.data[0]["orders"]), 2)

    def test_list_orders_completed_phase(self):
        self.phase.status = models.Phase.COMPLETED
        self.phase.save()
        response = self.create_request(self.game.id, self.phase.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert the response contains orders for both nations
        self.assertEqual(len(response.data), 2)
        nations = {entry["nation"] for entry in response.data}
        self.assertIn(self.member.nation, nations)
        self.assertIn(self.other_member.nation, nations)

    def test_list_orders_invalid_phase(self):
        response = self.create_request(self.game.id, 999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
