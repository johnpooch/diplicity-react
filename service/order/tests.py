import json
import pytest
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase
from django.core import exceptions
from rest_framework import status
from common.constants import PhaseStatus, OrderType, UnitType, OrderCreationStep, OrderResolutionStatus, PhaseType

from .models import Order, OrderResolution
from .utils import get_options_for_order, get_order_data_from_selected


class TestOrderListView:

    @pytest.mark.django_db
    def test_list_orders_active_phase_primary_user_has_order(
        self,
        authenticated_client,
        order_active_game,
        primary_user,
        classical_london_province,
        classical_english_channel_province,
    ):
        game = order_active_game
        phase = game.current_phase
        phase_state = phase.phase_states.get(member__user=primary_user)
        Order.objects.create(
            phase_state=phase_state,
            order_type=OrderType.MOVE,
            source=classical_london_province,
            target=classical_english_channel_province,
        )

        url = reverse("order-list", args=[game.id, game.current_phase.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        assert response.data[0]["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data[0]["order_type"] == OrderType.MOVE

        assert response.data[0]["source"]["id"] == "lon"
        assert response.data[0]["source"]["name"] == "London"
        assert response.data[0]["source"]["type"] == "coastal"
        assert response.data[0]["source"]["supply_center"] == True

        assert response.data[0]["target"]["id"] == "eng"
        assert response.data[0]["target"]["name"] == "English Channel"
        assert response.data[0]["target"]["type"] == "sea"
        assert response.data[0]["target"]["supply_center"] == False

        assert response.data[0]["aux"] is None
        assert response.data[0]["resolution"] is None
        assert response.data[0]["unit_type"] is None

    @pytest.mark.django_db
    def test_list_orders_active_phase_secondary_user_has_order(
        self,
        authenticated_client,
        order_active_game,
        secondary_user,
        classical_paris_province,
        classical_burgundy_province,
    ):
        game = order_active_game
        phase = game.current_phase
        phase_state = phase.phase_states.get(member__user=secondary_user)
        Order.objects.create(
            phase_state=phase_state,
            order_type=OrderType.MOVE,
            source=classical_paris_province,
            target=classical_burgundy_province,
        )

        url = reverse("order-list", args=[game.id, game.current_phase.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    @pytest.mark.django_db
    def test_list_orders_completed_phase_both_users_have_orders(
        self,
        authenticated_client,
        order_active_game,
        primary_user,
        secondary_user,
        classical_london_province,
        classical_english_channel_province,
        classical_paris_province,
        classical_burgundy_province,
    ):
        game = order_active_game
        phase = game.current_phase

        primary_phase_state = phase.phase_states.get(member__user=primary_user)
        secondary_phase_state = phase.phase_states.get(member__user=secondary_user)

        primary_order = Order.objects.create(
            phase_state=primary_phase_state,
            order_type=OrderType.MOVE,
            source=classical_london_province,
            target=classical_english_channel_province,
        )
        secondary_order = Order.objects.create(
            phase_state=secondary_phase_state,
            order_type=OrderType.MOVE,
            source=classical_paris_province,
            target=classical_burgundy_province,
        )
        OrderResolution.objects.create(order=primary_order, status=OrderResolutionStatus.SUCCEEDED, by=None)
        OrderResolution.objects.create(
            order=secondary_order, status=OrderResolutionStatus.BOUNCED, by=classical_burgundy_province
        )

        phase.status = PhaseStatus.COMPLETED
        phase.save()

        url = reverse("order-list", args=[game.id, phase.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        orders_by_nation = {order["nation"]["name"]: order for order in response.data}

        england_order = orders_by_nation["England"]
        assert england_order["resolution"]["status"] == "Succeeded"
        assert england_order["resolution"]["by"] is None

        france_order = orders_by_nation["France"]
        assert france_order["resolution"]["status"] == "Bounced"
        assert france_order["resolution"]["by"]["id"] == "bur"

    @pytest.mark.django_db
    def test_list_orders_invalid_phase(self, authenticated_client, order_active_game):
        game = order_active_game
        url = reverse("order-list", args=[game.id, 999])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_list_orders_unauthorized(self, unauthenticated_client, order_active_game):
        game = order_active_game
        url = reverse("order-list", args=[game.id, game.current_phase.id])
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestOrderCreateView:

    @pytest.mark.django_db
    def test_order_create_empty_selected(self, authenticated_client, game_with_options):
        url = reverse("order-create", args=[game_with_options.id])
        data = {"selected": []}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_order_create_source(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud"]}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 0

        assert response.data["selected"] == ["bud"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is False
        assert response.data["order_type"] is None
        assert response.data["unit_type"] is None
        assert response.data["target"] is None
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == [
            {"value": "Hold", "label": "Hold"},
            {"value": "Move", "label": "Move"},
            {"value": "Support", "label": "Support"},
        ]
        assert response.data["step"] == OrderCreationStep.SELECT_ORDER_TYPE
        assert response.data["title"] == "Select order type for Budapest"

    @pytest.mark.django_db
    def test_order_create_invalid_source(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["invalid"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_create_invalid_order_type(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Invalid"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_order_create_move_with_source(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Move"]}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 0

        assert response.data["selected"] == ["bud", "Move"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is False
        assert response.data["order_type"] == "Move"
        assert response.data["unit_type"] is None
        assert response.data["target"] is None
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == [
            {"value": "gal", "label": "Galicia"},
            {"value": "rum", "label": "Rumania"},
            {"value": "ser", "label": "Serbia"},
            {"value": "tri", "label": "Trieste"},
            {"value": "vie", "label": "Vienna"},
        ]
        assert response.data["step"] == OrderCreationStep.SELECT_TARGET
        assert response.data["title"] == "Select province to move Budapest to"

    def test_order_create_move_with_source_and_target(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Move", "gal"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1

        assert response.data["selected"] == ["bud", "Move", "gal"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is True
        assert response.data["order_type"] == "Move"
        assert response.data["unit_type"] is None
        assert response.data["target"]["id"] == "gal"
        assert response.data["target"]["name"] == "Galicia"
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == []
        assert response.data["step"] == OrderCreationStep.COMPLETED
        assert response.data["title"] == "Budapest will move to Galicia"

    def test_order_create_move_with_invalid_target(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Move", "invalid"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_create_support_with_source(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Support"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 0

        assert response.data["selected"] == ["bud", "Support"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is False
        assert response.data["order_type"] == "Support"
        assert response.data["unit_type"] is None
        assert response.data["target"] is None
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == [
            {"value": "sev", "label": "Sevastopol"},
            {"value": "tri", "label": "Trieste"},
            {"value": "vie", "label": "Vienna"},
        ]
        assert response.data["step"] == OrderCreationStep.SELECT_AUX
        assert response.data["title"] == "Select province for Budapest to support"

    def test_order_create_support_with_source_and_aux(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Support", "vie"]}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 0

        assert response.data["selected"] == ["bud", "Support", "vie"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is False
        assert response.data["order_type"] == "Support"
        assert response.data["unit_type"] is None
        assert response.data["target"] is None
        assert response.data["aux"]["id"] == "vie"
        assert response.data["aux"]["name"] == "Vienna"
        assert response.data["resolution"] is None
        assert response.data["options"] == [
            {"value": "gal", "label": "Galicia"},
            {"value": "tri", "label": "Trieste"},
            {"value": "vie", "label": "Vienna"},
        ]
        assert response.data["step"] == OrderCreationStep.SELECT_TARGET
        assert response.data["title"] == "Select destination for Budapest to support Vienna to"

    def test_order_create_support_with_invalid_aux(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Support", "invalid"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_create_support_with_source_and_aux_and_target(
        self, authenticated_client, game_with_options, primary_user
    ):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Support", "vie", "tri"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1

        assert response.data["selected"] == ["bud", "Support", "vie", "tri"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is True
        assert response.data["order_type"] == "Support"
        assert response.data["unit_type"] is None
        assert response.data["target"]["id"] == "tri"
        assert response.data["target"]["name"] == "Trieste"
        assert response.data["aux"]["id"] == "vie"
        assert response.data["aux"]["name"] == "Vienna"
        assert response.data["resolution"] is None
        assert response.data["options"] == []
        assert response.data["step"] == OrderCreationStep.COMPLETED
        assert response.data["title"] == "Budapest will support Vienna to Trieste"

    def test_order_create_hold_with_source(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Hold"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1

        assert response.data["selected"] == ["bud", "Hold"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is True
        assert response.data["order_type"] == "Hold"
        assert response.data["unit_type"] is None
        assert response.data["target"] is None
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == []
        assert response.data["step"] == OrderCreationStep.COMPLETED
        assert response.data["title"] == "Budapest will hold"

    def test_order_create_build_with_source(self, authenticated_client, game_with_options, primary_user):
        phase = game_with_options.current_phase
        sample_options = {
            "England": {
                "bud": {
                    "Next": {
                        "Build": {
                            "Next": {
                                "Army": {"Next": {}, "Type": "UnitType"},
                                "Fleet": {"Next": {}, "Type": "UnitType"},
                            },
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.options = sample_options
        phase.save()
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Build"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 0

        assert response.data["selected"] == ["bud", "Build"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is False
        assert response.data["order_type"] == "Build"
        assert response.data["unit_type"] is None
        assert response.data["target"] is None
        assert response.data["aux"] is None
        assert response.data["options"] == [
            {"value": "Army", "label": "Army"},
            {"value": "Fleet", "label": "Fleet"},
        ]
        assert response.data["step"] == OrderCreationStep.SELECT_UNIT_TYPE
        assert response.data["title"] == "Select unit type to build in Budapest"

    def test_order_create_build_with_source_and_unit_type(self, authenticated_client, game_with_options, primary_user):
        phase = game_with_options.current_phase
        sample_options = {
            "England": {
                "bud": {
                    "Next": {
                        "Build": {
                            "Next": {
                                "Army": {"Next": {}, "Type": "UnitType"},
                                "Fleet": {"Next": {}, "Type": "UnitType"},
                            },
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.options = sample_options
        phase.save()
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Build", "Army"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1

        assert response.data["selected"] == ["bud", "Build", "Army"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is True
        assert response.data["order_type"] == "Build"
        assert response.data["unit_type"] == "Army"
        assert response.data["target"] is None
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == []
        assert response.data["step"] == OrderCreationStep.COMPLETED
        assert response.data["title"] == "Army will be built in Budapest"

    def test_order_create_move_via_convoy_with_source(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        
        # Update options to include MoveViaConvoy
        phase = game.current_phase
        sample_options = phase.options.copy()
        sample_options["England"]["bud"]["Next"]["MoveViaConvoy"] = sample_options["England"]["bud"]["Next"]["Move"]
        phase.options = sample_options
        phase.save()
        
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "MoveViaConvoy"]}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 0

        assert response.data["selected"] == ["bud", "MoveViaConvoy"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is False
        assert response.data["order_type"] == "MoveViaConvoy"
        assert response.data["unit_type"] is None
        assert response.data["target"] is None
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == [
            {"value": "gal", "label": "Galicia"},
            {"value": "rum", "label": "Rumania"},
            {"value": "ser", "label": "Serbia"},
            {"value": "tri", "label": "Trieste"},
            {"value": "vie", "label": "Vienna"},
        ]
        assert response.data["step"] == OrderCreationStep.SELECT_TARGET
        assert response.data["title"] == "Select province to move Budapest to"

    def test_order_create_move_via_convoy_with_source_and_target(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        
        # Update options to include MoveViaConvoy
        phase = game.current_phase
        sample_options = phase.options.copy()
        sample_options["England"]["bud"]["Next"]["MoveViaConvoy"] = sample_options["England"]["bud"]["Next"]["Move"]
        phase.options = sample_options
        phase.save()
        
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "MoveViaConvoy", "gal"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1

        assert response.data["selected"] == ["bud", "MoveViaConvoy", "gal"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is True
        assert response.data["order_type"] == "MoveViaConvoy"
        assert response.data["unit_type"] is None
        assert response.data["target"]["id"] == "gal"
        assert response.data["target"]["name"] == "Galicia"
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == []
        assert response.data["step"] == OrderCreationStep.COMPLETED
        assert response.data["title"] == "Budapest will move via convoy to Galicia"

    def test_order_create_move_via_convoy_with_invalid_target(self, authenticated_client, game_with_options, primary_user):
        game = game_with_options
        
        # Update options to include MoveViaConvoy
        phase = game.current_phase
        sample_options = phase.options.copy()
        sample_options["England"]["bud"]["Next"]["MoveViaConvoy"] = sample_options["England"]["bud"]["Next"]["Move"]
        phase.options = sample_options
        phase.save()
        
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "MoveViaConvoy", "invalid"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_create_disband_with_source(self, authenticated_client, game_with_options, primary_user):
        phase = game_with_options.current_phase
        sample_options = {
            "England": {
                "bud": {
                    "Next": {
                        "Disband": {
                            "Next": {
                                "bud": {"Next": {}, "Type": "SrcProvince"},
                            },
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.options = sample_options
        phase.save()
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Disband"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1

        assert response.data["selected"] == ["bud", "Disband"]
        assert response.data["source"]["id"] == "bud"
        assert response.data["source"]["name"] == "Budapest"
        assert response.data["nation"] == {"name": "England", "color": "#2196F3"}
        assert response.data["complete"] is True
        assert response.data["order_type"] == "Disband"
        assert response.data["unit_type"] is None
        assert response.data["target"] is None
        assert response.data["aux"] is None
        assert response.data["resolution"] is None
        assert response.data["options"] == []
        assert response.data["step"] == OrderCreationStep.COMPLETED
        assert response.data["title"] == "Budapest will be disbanded"

    def test_order_create_replaces_existing_order_for_same_province(
        self, authenticated_client, game_with_options, primary_user
    ):
        game = game_with_options
        url = reverse("order-create", args=[game.id])

        # Create first order for Budapest
        data = {"selected": ["bud", "Hold"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1
        first_order = Order.objects.first()
        assert first_order.order_type == "Hold"

        # Create second order for Budapest - should replace the first
        data = {"selected": ["bud", "Move", "gal"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1  # Still only one order

        # Verify the order was replaced
        second_order = Order.objects.first()
        assert second_order.order_type == "Move"
        assert second_order.target.province_id == "gal"
        assert second_order.id != first_order.id  # Different order instance

    def test_order_create_partial_order_does_not_replace_existing_complete_order(
        self, authenticated_client, game_with_options, primary_user
    ):
        game = game_with_options
        url = reverse("order-create", args=[game.id])

        # Create complete order for Budapest
        data = {"selected": ["bud", "Move", "gal"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1
        first_order = Order.objects.first()
        assert first_order.complete is True

        # Start new order for same province - should NOT delete the complete order
        data = {"selected": ["bud"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1  # Original order still exists since partial orders are not saved

        # Complete the new order - this should replace the existing order
        data = {"selected": ["bud", "Hold"]}
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1

        second_order = Order.objects.first()
        assert second_order.order_type == "Hold"
        assert second_order.id != first_order.id


class TestOrderDeleteView:
    @pytest.mark.django_db
    def test_delete_order_success(
        self,
        authenticated_client,
        order_active_game,
        primary_user,
        classical_london_province,
    ):
        game = order_active_game
        phase = game.current_phase
        phase_state = phase.phase_states.get(member__user=primary_user)

        # Create an order to delete
        Order.objects.create(
            phase_state=phase_state,
            order_type=OrderType.HOLD,
            source=classical_london_province,
        )

        assert Order.objects.count() == 1

        url = reverse("order-delete", args=[game.id, "lon"])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Order.objects.count() == 0

    @pytest.mark.django_db
    def test_delete_order_not_found(
        self,
        authenticated_client,
        order_active_game,
    ):
        game = order_active_game

        url = reverse("order-delete", args=[game.id, "lon"])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_delete_order_unauthenticated(self, client, order_active_game):
        game = order_active_game

        url = reverse("order-delete", args=[game.id, "lon"])
        response = client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestOrderListViewQueryPerformance:

    @pytest.mark.django_db
    def test_list_orders_query_count_with_one_order(
        self,
        authenticated_client,
        order_active_game,
        primary_user,
        secondary_user,
        classical_london_province,
        classical_english_channel_province,
    ):
        game = order_active_game
        phase = game.current_phase
        primary_phase_state = phase.phase_states.get(member__user=primary_user)
        Order.objects.create(
            phase_state=primary_phase_state,
            order_type=OrderType.MOVE,
            source=classical_london_province,
            target=classical_english_channel_province,
        )
        url = reverse("order-list", args=[game.id, phase.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(connection.queries) == 9

    @pytest.mark.django_db
    def test_list_orders_query_count_with_multiple_orders(
        self,
        authenticated_client,
        order_active_game,
        primary_user,
        secondary_user,
        classical_london_province,
        classical_english_channel_province,
        classical_paris_province,
        classical_burgundy_province,
    ):
        game = order_active_game
        phase = game.current_phase
        primary_phase_state = phase.phase_states.get(member__user=primary_user)
        secondary_phase_state = phase.phase_states.get(member__user=secondary_user)
        Order.objects.create(
            phase_state=primary_phase_state,
            order_type=OrderType.MOVE,
            source=classical_london_province,
            target=classical_english_channel_province,
        )
        Order.objects.create(
            phase_state=secondary_phase_state,
            order_type=OrderType.MOVE,
            source=classical_paris_province,
            target=classical_burgundy_province,
        )
        url = reverse("order-list", args=[game.id, phase.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(connection.queries) == 9


class TestOrderCreateViewQueryPerformance:

    @pytest.mark.django_db
    def test_order_create_query_count(self, authenticated_client, game_with_options):
        game = game_with_options
        url = reverse("order-create", args=[game.id])
        data = {"selected": ["bud", "Move", "gal"]}

        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        query_count = len(connection.queries)

        assert query_count == 19


class TestGetOptionsForOrder:

    @pytest.mark.django_db
    def test_no_source_returns_nation_provinces(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source=None, order_type=None, target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert "bud" in options
        assert "tri" in options
        assert len(options) == 2

    @pytest.mark.django_db
    def test_with_source_only_returns_order_types(self, sample_options, test_phase_state, classical_budapest_province):
        order = Order(
            phase_state=test_phase_state, source=classical_budapest_province, order_type=None, target=None, aux=None
        )
        options = get_options_for_order(sample_options, order)
        assert "Hold" in options
        assert "Move" in options
        assert "Support" in options
        assert len(options) == 3

    @pytest.mark.django_db
    def test_with_source_and_move_order_type_returns_targets(
        self, sample_options, test_phase_state, classical_budapest_province
    ):
        order = Order(
            phase_state=test_phase_state, source=classical_budapest_province, order_type="Move", target=None, aux=None
        )
        options = get_options_for_order(sample_options, order)
        assert "gal" in options
        assert "rum" in options
        assert "ser" in options
        assert "tri" in options
        assert "vie" in options
        assert len(options) == 5

    @pytest.mark.django_db
    def test_hold_order_with_all_fields_returns_empty_list(
        self, sample_options, test_phase_state, classical_budapest_province
    ):
        order = Order(
            phase_state=test_phase_state, source=classical_budapest_province, order_type="Hold", target=None, aux=None
        )
        options = get_options_for_order(sample_options, order)
        assert options == []

    @pytest.mark.django_db
    def test_move_order_with_all_fields_returns_empty_list(
        self, sample_options, test_phase_state, classical_budapest_province, classical_trieste_province
    ):
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type="Move",
            target=classical_trieste_province,
            aux=None,
        )
        options = get_options_for_order(sample_options, order)
        assert options == []

    @pytest.mark.django_db
    def test_support_order_with_all_fields_returns_empty_list(
        self, sample_options, test_phase_state, classical_budapest_province, classical_trieste_province
    ):
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type="Support",
            target=classical_trieste_province,
            aux=classical_trieste_province,
        )
        options = get_options_for_order(sample_options, order)
        assert options == []

    @pytest.mark.django_db
    def test_invalid_source_raises_error(self, sample_options, test_phase_state, classical_london_province):
        order = Order(
            phase_state=test_phase_state, source=classical_london_province, order_type=None, target=None, aux=None
        )
        with pytest.raises(ValueError, match="Source province lon not found in options"):
            get_options_for_order(sample_options, order)

    @pytest.mark.django_db
    def test_invalid_order_type_raises_error(self, sample_options, test_phase_state, classical_budapest_province):
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type="InvalidType",
            target=None,
            aux=None,
        )
        with pytest.raises(ValueError, match="Order type InvalidType not found in options"):
            get_options_for_order(sample_options, order)

    @pytest.mark.django_db
    def test_invalid_target_raises_error(
        self, sample_options, test_phase_state, classical_budapest_province, classical_london_province
    ):
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type="Move",
            target=classical_london_province,
            aux=None,
        )
        with pytest.raises(ValueError, match="Target province lon not found in options"):
            get_options_for_order(sample_options, order)

    @pytest.mark.django_db
    def test_invalid_aux_raises_error(
        self,
        sample_options,
        test_phase_state,
        classical_budapest_province,
        classical_trieste_province,
        classical_london_province,
    ):
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type="Support",
            target=classical_trieste_province,
            aux=classical_london_province,
        )
        with pytest.raises(ValueError, match="Auxiliary province lon not found in options"):
            get_options_for_order(sample_options, order)

    @pytest.mark.django_db
    def test_nested_support_order_options(self, sample_options, test_phase_state, classical_budapest_province):
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type=OrderType.SUPPORT,
            target=None,
            aux=None,
        )
        options = get_options_for_order(sample_options, order)
        assert "sev" in options
        assert "tri" in options
        assert "vie" in options
        assert len(options) == 3

    @pytest.mark.django_db
    def test_support_order_target_selection_after_aux(
        self, sample_options, test_phase_state, classical_budapest_province, classical_vienna_province
    ):
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type=OrderType.SUPPORT,
            target=None,
            aux=classical_vienna_province,
        )
        options = get_options_for_order(sample_options, order)
        assert "gal" in options
        assert "tri" in options
        assert "vie" in options
        assert len(options) == 3

    @pytest.mark.django_db
    def test_empty_options_structure(self, test_phase_state, classical_budapest_province):
        empty_options = {}
        order = Order(phase_state=test_phase_state, source=None, order_type=None, target=None, aux=None)

        with pytest.raises(KeyError):
            get_options_for_order(empty_options, order)

    @pytest.mark.django_db
    def test_convoy_order_structure(self, sample_options, test_phase_state, classical_budapest_province):
        sample_options["England"]["bud"]["Next"]["Convoy"] = {
            "Next": {
                "bud": {
                    "Next": {"sev": {"Next": {"rum": {"Next": {}, "Type": "Province"}}, "Type": "Province"}},
                    "Type": "SrcProvince",
                }
            },
            "Type": "OrderType",
        }
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type=OrderType.CONVOY,
            target=None,
            aux=None,
        )
        options = get_options_for_order(sample_options, order)
        assert "sev" in options
        assert len(options) == 1

    @pytest.mark.django_db
    def test_build_order_structure(self, sample_options, test_phase_state, classical_budapest_province):
        sample_options["England"]["bud"]["Next"]["Build"] = {
            "Next": {
                "bud": {
                    "Next": {"Army": {"Next": {}, "Type": "UnitType"}, "Fleet": {"Next": {}, "Type": "UnitType"}},
                    "Type": "SrcProvince",
                }
            },
            "Type": "OrderType",
        }
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type=OrderType.BUILD,
            target=None,
            aux=None,
        )
        options = get_options_for_order(sample_options, order)
        assert "Army" in options
        assert "Fleet" in options
        assert len(options) == 2

    @pytest.mark.django_db
    def test_disband_order_structure(self, sample_options, test_phase_state, classical_budapest_province):
        sample_options["England"]["bud"]["Next"]["Disband"] = {
            "Next": {"bud": {"Next": {}, "Type": "SrcProvince"}},
            "Type": "OrderType",
        }
        order = Order(
            phase_state=test_phase_state,
            source=classical_budapest_province,
            order_type=OrderType.DISBAND,
            target=None,
            aux=None,
        )
        options = get_options_for_order(sample_options, order)
        assert options == []


class TestOrderManagerMethods:

    @pytest.mark.django_db
    def test_for_source_in_phase_returns_correct_orders(
        self, test_phase_state, classical_budapest_province, classical_trieste_province
    ):
        order1 = Order.objects.create(
            phase_state=test_phase_state, source=classical_budapest_province, order_type="Hold"
        )
        order2 = Order.objects.create(
            phase_state=test_phase_state, source=classical_trieste_province, order_type="Hold"
        )

        budapest_orders = Order.objects.for_source_in_phase(test_phase_state, classical_budapest_province)
        assert budapest_orders.count() == 1
        assert budapest_orders.first() == order1

        trieste_orders = Order.objects.for_source_in_phase(test_phase_state, classical_trieste_province)
        assert trieste_orders.count() == 1
        assert trieste_orders.first() == order2

    @pytest.mark.django_db
    def test_delete_existing_for_source_removes_correct_orders(
        self, test_phase_state, classical_budapest_province, classical_trieste_province
    ):
        order1 = Order.objects.create(
            phase_state=test_phase_state, source=classical_budapest_province, order_type="Hold"
        )
        order2 = Order.objects.create(
            phase_state=test_phase_state, source=classical_trieste_province, order_type="Hold"
        )

        assert Order.objects.count() == 2

        Order.objects.delete_existing_for_source(test_phase_state, classical_budapest_province)

        assert Order.objects.count() == 1
        remaining_order = Order.objects.first()
        assert remaining_order == order2
        assert remaining_order.source == classical_trieste_province


class TestOrderComplete:

    @pytest.mark.django_db
    def test_hold_order_is_always_complete(self, test_phase_state, classical_london_province):
        order = Order(phase_state=test_phase_state, order_type=OrderType.HOLD, source=classical_london_province)
        assert order.complete is True

    @pytest.mark.django_db
    def test_disband_order_is_always_complete(self, test_phase_state, classical_london_province):
        order = Order(phase_state=test_phase_state, order_type=OrderType.DISBAND, source=classical_london_province)
        assert order.complete is True

    @pytest.mark.django_db
    def test_move_order_complete_when_target_set(
        self, test_phase_state, classical_london_province, classical_english_channel_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.MOVE,
            source=classical_london_province,
            target=classical_english_channel_province,
        )
        assert order.complete is True

    @pytest.mark.django_db
    def test_move_order_incomplete_when_target_none(self, test_phase_state, classical_london_province):
        order = Order(
            phase_state=test_phase_state, order_type=OrderType.MOVE, source=classical_london_province, target=None
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_build_order_complete_when_unit_type_set(self, test_phase_state, classical_london_province):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.BUILD,
            source=classical_london_province,
            unit_type=UnitType.FLEET,
        )
        assert order.complete is True

        order_army = Order(
            phase_state=test_phase_state,
            order_type=OrderType.BUILD,
            source=classical_london_province,
            unit_type=UnitType.ARMY,
        )
        assert order_army.complete is True

    @pytest.mark.django_db
    def test_build_order_incomplete_when_unit_type_none(self, test_phase_state, classical_london_province):
        order = Order(
            phase_state=test_phase_state, order_type=OrderType.BUILD, source=classical_london_province, unit_type=None
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_support_order_complete_when_target_and_aux_set(
        self, test_phase_state, classical_london_province, classical_english_channel_province, classical_spain_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.SUPPORT,
            source=classical_london_province,
            target=classical_english_channel_province,
            aux=classical_spain_province,
        )
        assert order.complete is True

    @pytest.mark.django_db
    def test_support_order_incomplete_when_target_none(
        self, test_phase_state, classical_london_province, classical_spain_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.SUPPORT,
            source=classical_london_province,
            target=None,
            aux=classical_spain_province,
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_support_order_incomplete_when_aux_none(
        self, test_phase_state, classical_london_province, classical_english_channel_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.SUPPORT,
            source=classical_london_province,
            target=classical_english_channel_province,
            aux=None,
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_support_order_incomplete_when_both_target_and_aux_none(self, test_phase_state, classical_london_province):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.SUPPORT,
            source=classical_london_province,
            target=None,
            aux=None,
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_convoy_order_complete_when_target_and_aux_set(
        self, test_phase_state, classical_english_channel_province, classical_london_province, classical_spain_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.CONVOY,
            source=classical_english_channel_province,
            target=classical_london_province,
            aux=classical_spain_province,
        )
        assert order.complete is True

    @pytest.mark.django_db
    def test_convoy_order_incomplete_when_target_none(
        self, test_phase_state, classical_english_channel_province, classical_spain_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.CONVOY,
            source=classical_english_channel_province,
            target=None,
            aux=classical_spain_province,
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_convoy_order_incomplete_when_aux_none(
        self, test_phase_state, classical_english_channel_province, classical_london_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.CONVOY,
            source=classical_english_channel_province,
            target=classical_london_province,
            aux=None,
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_move_via_convoy_order_complete_when_target_set(
        self, test_phase_state, classical_london_province, classical_english_channel_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.MOVE_VIA_CONVOY,
            source=classical_london_province,
            target=classical_english_channel_province,
        )
        assert order.complete is True

    @pytest.mark.django_db
    def test_move_via_convoy_order_incomplete_when_target_none(self, test_phase_state, classical_london_province):
        order = Order(
            phase_state=test_phase_state, order_type=OrderType.MOVE_VIA_CONVOY, source=classical_london_province, target=None
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_convoy_order_incomplete_when_both_target_and_aux_none(
        self, test_phase_state, classical_english_channel_province
    ):
        order = Order(
            phase_state=test_phase_state,
            order_type=OrderType.CONVOY,
            source=classical_english_channel_province,
            target=None,
            aux=None,
        )
        assert order.complete is False

    @pytest.mark.django_db
    def test_order_complete_with_none_order_type(self, test_phase_state, classical_london_province):
        order = Order(phase_state=test_phase_state, order_type=None, source=classical_london_province)
        assert order.complete is False


class TestGetOrderDataFromSelected:

    def test_empty_selected_returns_empty_dict(self):
        result = get_order_data_from_selected([])
        assert result == {}

    def test_none_selected_returns_empty_dict(self):
        result = get_order_data_from_selected(None)
        assert result == {}

    def test_only_source_returns_source(self):
        result = get_order_data_from_selected(["ber"])
        assert result == {"source": "ber"}

    def test_move_order_complete(self):
        result = get_order_data_from_selected(["ber", OrderType.MOVE, "kie"])
        expected = {"source": "ber", "order_type": OrderType.MOVE, "target": "kie"}
        assert result == expected

    def test_move_order_incomplete(self):
        result = get_order_data_from_selected(["ber", OrderType.MOVE])
        expected = {"source": "ber", "order_type": OrderType.MOVE}
        assert result == expected

    def test_build_order_complete(self):
        result = get_order_data_from_selected(["ber", OrderType.BUILD, UnitType.ARMY])
        expected = {"source": "ber", "order_type": OrderType.BUILD, "unit_type": UnitType.ARMY}
        assert result == expected

    def test_build_order_incomplete(self):
        result = get_order_data_from_selected(["ber", OrderType.BUILD])
        expected = {"source": "ber", "order_type": OrderType.BUILD}
        assert result == expected

    def test_support_order_complete(self):
        result = get_order_data_from_selected(["ber", OrderType.SUPPORT, "pru", "war"])
        expected = {"source": "ber", "order_type": OrderType.SUPPORT, "aux": "pru", "target": "war"}
        assert result == expected

    def test_support_order_partial_aux_only(self):
        result = get_order_data_from_selected(["ber", OrderType.SUPPORT, "pru"])
        expected = {"source": "ber", "order_type": OrderType.SUPPORT, "aux": "pru"}
        assert result == expected

    def test_support_order_incomplete(self):
        result = get_order_data_from_selected(["ber", OrderType.SUPPORT])
        expected = {"source": "ber", "order_type": OrderType.SUPPORT}
        assert result == expected

    def test_convoy_order_complete(self):
        result = get_order_data_from_selected(["eng", OrderType.CONVOY, "lon", "bre"])
        expected = {"source": "eng", "order_type": OrderType.CONVOY, "aux": "lon", "target": "bre"}
        assert result == expected

    def test_convoy_order_partial_aux_only(self):
        result = get_order_data_from_selected(["eng", OrderType.CONVOY, "lon"])
        expected = {"source": "eng", "order_type": OrderType.CONVOY, "aux": "lon"}
        assert result == expected

    def test_convoy_order_incomplete(self):
        result = get_order_data_from_selected(["eng", OrderType.CONVOY])
        expected = {"source": "eng", "order_type": OrderType.CONVOY}
        assert result == expected

    def test_hold_order(self):
        result = get_order_data_from_selected(["ber", OrderType.HOLD])
        expected = {"source": "ber", "order_type": OrderType.HOLD}
        assert result == expected

    def test_move_via_convoy_order_complete(self):
        result = get_order_data_from_selected(["ber", OrderType.MOVE_VIA_CONVOY, "kie"])
        expected = {"source": "ber", "order_type": OrderType.MOVE_VIA_CONVOY, "target": "kie"}
        assert result == expected

    def test_move_via_convoy_order_incomplete(self):
        result = get_order_data_from_selected(["ber", OrderType.MOVE_VIA_CONVOY])
        expected = {"source": "ber", "order_type": OrderType.MOVE_VIA_CONVOY}
        assert result == expected

    def test_disband_order(self):
        result = get_order_data_from_selected(["ber", OrderType.DISBAND])
        expected = {"source": "ber", "order_type": OrderType.DISBAND}
        assert result == expected


class TestOrderValidationLimits:
    """
    Test Order model validation for adjustment phase limits.
    """

    @pytest.mark.django_db
    def test_validation_allows_orders_under_limit(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        """Test that orders are allowed when under the adjustment phase limit."""
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.ordinal = phase.ordinal + 1
        phase.options = {
            "England": {
                "lon": {
                    "Next": {
                        "Build": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.save()

        # Nation can build 1 order (2 supply centers, 1 unit)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()

        # Should be able to create one order without validation error
        order = Order(phase_state=phase_state, source=classical_london_province, order_type=OrderType.BUILD)
        # This should not raise ValidationError
        order.clean()

    @pytest.mark.django_db
    def test_validation_prevents_orders_at_limit(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        """Test that ValidationError is raised when trying to create orders beyond the limit."""
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {
            "England": {
                "lon": {
                    "Next": {
                        "Build": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
                "par": {
                    "Next": {
                        "Build": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.ordinal = phase.ordinal + 1
        phase.save()

        # Nation can build 1 order (2 supply centers, 1 unit)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()

        # Create first order (at limit)
        first_order = Order.objects.create(
            phase_state=phase_state, source=classical_london_province, order_type=OrderType.BUILD
        )

        # Try to create second order - should raise ValidationError
        second_order = Order(phase_state=phase_state, source=classical_paris_province, order_type=OrderType.BUILD)

        with pytest.raises(
            exceptions.ValidationError, match="Cannot create order: nation has reached maximum of 1 orders"
        ):
            second_order.clean()

    @pytest.mark.django_db
    def test_validation_balanced_nation_no_orders_allowed(
        self, active_game_with_phase_state, classical_england_nation, classical_london_province
    ):
        """Test that balanced nations cannot create any orders."""
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.ordinal = phase.ordinal + 1
        phase.options = {
            "England": {
                "lon": {
                    "Next": {
                        "Build": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.save()

        # Nation has balanced supply centers and units (0 orders allowed)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()

        # Try to create order - should raise ValidationError
        order = Order(phase_state=phase_state, source=classical_london_province, order_type=OrderType.BUILD)

        with pytest.raises(
            exceptions.ValidationError, match="Cannot create order: nation has reached maximum of 0 orders"
        ):
            order.clean()

    @pytest.mark.django_db
    def test_validation_allows_order_updates(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        """Test that existing orders can be updated without triggering validation errors."""
        phase = active_game_with_phase_state.current_phase
        phase.ordinal = phase.ordinal + 1
        phase.options = {
            "England": {
                "lon": {
                    "Next": {
                        "Build": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                        "Disband": {
                            "Next": {"bud": {"Next": {}, "Type": "SrcProvince"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.type = PhaseType.ADJUSTMENT
        phase.save()

        # Nation can build 1 order (2 supply centers, 1 unit)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()

        # Create order (at limit)
        existing_order = Order.objects.create(
            phase_state=phase_state, source=classical_london_province, order_type=OrderType.BUILD
        )

        # Update the existing order - should not raise ValidationError
        existing_order.order_type = OrderType.DISBAND
        existing_order.clean()  # This should pass

    @pytest.mark.django_db
    def test_validation_multiple_builds_allowed_under_limit(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
        classical_edinburgh_province,
    ):
        """Test that multiple orders are allowed when under the limit."""
        phase = active_game_with_phase_state.current_phase
        phase.ordinal = phase.ordinal + 1
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {
            "England": {
                "lon": {
                    "Next": {
                        "Build": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
                "par": {
                    "Next": {
                        "Build": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
                "edi": {
                    "Next": {
                        "Build": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.save()

        # Nation has 3 supply centers but 0 units (can build 3)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

        phase_state = phase.phase_states.first()

        # Should be able to create first order
        order1 = Order(phase_state=phase_state, source=classical_london_province, order_type=OrderType.BUILD)
        order1.clean()  # Should pass
        order1.save()

        # Should be able to create second order
        order2 = Order(phase_state=phase_state, source=classical_paris_province, order_type=OrderType.BUILD)
        order2.clean()  # Should pass
        order2.save()

        # Should be able to create third order
        order3 = Order(phase_state=phase_state, source=classical_edinburgh_province, order_type=OrderType.BUILD)
        order3.clean()  # Should pass

    @pytest.mark.django_db
    def test_validation_disband_scenario(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        """Test validation for disband scenarios (surplus units)."""
        phase = active_game_with_phase_state.current_phase
        phase.ordinal = phase.ordinal + 1
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {
            "England": {
                "lon": {
                    "Next": {
                        "Disband": {
                            "Next": {"bud": {"Next": {}, "Type": "SrcProvince"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
                "par": {
                    "Next": {
                        "Disband": {
                            "Next": {"Army": {"Next": {}, "Type": "UnitType"}},
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                },
            },
        }
        phase.save()

        # Nation has 1 supply center but 2 units (must disband 1)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Army", nation=classical_england_nation, province=classical_paris_province)

        phase_state = phase.phase_states.first()

        # Should be able to create one disband order
        order1 = Order(phase_state=phase_state, source=classical_london_province, order_type=OrderType.DISBAND)
        order1.clean()  # Should pass
        order1.save()

        # Try to create second disband order - should raise ValidationError
        order2 = Order(phase_state=phase_state, source=classical_paris_province, order_type=OrderType.DISBAND)

        with pytest.raises(
            exceptions.ValidationError, match="Cannot create order: nation has reached maximum of 1 orders"
        ):
            order2.clean()
