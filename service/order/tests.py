import json
import pytest
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase
from rest_framework import status
from common.constants import PhaseStatus, OrderType, UnitType, OrderCreationStep, OrderResolutionStatus

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

        assert query_count == 18


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

    def test_disband_order(self):
        result = get_order_data_from_selected(["ber", OrderType.DISBAND])
        expected = {"source": "ber", "order_type": OrderType.DISBAND}
        assert result == expected
