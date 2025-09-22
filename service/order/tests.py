import json
import pytest
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase
from rest_framework import status
from common.constants import PhaseStatus, OrderType, UnitType, OrderCreationStep

from .models import Order, OrderResolution
from .utils import get_options_for_order


class TestOrderListView:

    @pytest.mark.django_db
    def test_list_orders_active_phase_primary_user_has_order(self, authenticated_client, active_game, primary_user):
        game = active_game
        phase = game.current_phase
        phase_state = phase.phase_states.get(member__user=primary_user)
        Order.objects.create(phase_state=phase_state, order_type="Move", source="lon", target="eng")

        url = reverse("order-list", args=[game.id, game.current_phase.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        assert response.data[0]["nation"] == "England"
        assert response.data[0]["order_type"] == "Move"

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
    def test_list_orders_active_phase_secondary_user_has_order(self, authenticated_client, active_game, secondary_user):
        game = active_game
        phase = game.current_phase
        phase_state = phase.phase_states.get(member__user=secondary_user)
        Order.objects.create(phase_state=phase_state, order_type="Move", source="par", target="bur")

        url = reverse("order-list", args=[game.id, game.current_phase.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    @pytest.mark.django_db
    def test_list_orders_completed_phase_both_users_have_orders(
        self, authenticated_client, active_game, primary_user, secondary_user
    ):
        game = active_game
        phase = game.current_phase

        primary_phase_state = phase.phase_states.get(member__user=primary_user)
        secondary_phase_state = phase.phase_states.get(member__user=secondary_user)

        primary_order = Order.objects.create(
            phase_state=primary_phase_state, order_type="Move", source="lon", target="eng"
        )
        secondary_order = Order.objects.create(
            phase_state=secondary_phase_state, order_type="Move", source="par", target="bur"
        )
        OrderResolution.objects.create(order=primary_order, status="Succeeded", by=None)
        OrderResolution.objects.create(order=secondary_order, status="Bounced", by="bur")

        phase.status = PhaseStatus.COMPLETED
        phase.save()

        url = reverse("order-list", args=[game.id, phase.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        orders_by_nation = {order["nation"]: order for order in response.data}

        england_order = orders_by_nation["England"]
        assert england_order["resolution"]["status"] == "Succeeded"
        assert england_order["resolution"]["by"] is None

        france_order = orders_by_nation["France"]
        assert france_order["resolution"]["status"] == "Bounced"
        assert france_order["resolution"]["by"] == "bur"

    @pytest.mark.django_db
    def test_list_orders_invalid_phase(self, authenticated_client, active_game):
        game = active_game
        url = reverse("order-list", args=[game.id, 999])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_list_orders_unauthorized(self, unauthenticated_client, active_game):
        game = active_game
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
        assert response.data["nation"] == "England"
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
        assert response.data["nation"] == "England"
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
        assert response.data["nation"] == "England"
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
        assert response.data["nation"] == "England"
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
        assert response.data["nation"] == "England"
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
        assert response.data["nation"] == "England"
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
        assert response.data["nation"] == "England"
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
        phase.options = json.dumps(sample_options)
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
        assert response.data["nation"] == "England"
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
        phase.options = json.dumps(sample_options)
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
        assert response.data["nation"] == "England"
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
        phase.options = json.dumps(sample_options)
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
        assert response.data["nation"] == "England"
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
        self, authenticated_client, active_game, primary_user, secondary_user
    ):
        game = active_game
        phase = game.current_phase
        primary_phase_state = phase.phase_states.get(member__user=primary_user)
        Order.objects.create(phase_state=primary_phase_state, order_type="Move", source="lon", target="eng")
        url = reverse("order-list", args=[game.id, phase.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(connection.queries) == 3

    @pytest.mark.django_db
    def test_list_orders_query_count_with_multiple_orders(
        self, authenticated_client, active_game, primary_user, secondary_user
    ):
        game = active_game
        phase = game.current_phase
        primary_phase_state = phase.phase_states.get(member__user=primary_user)
        secondary_phase_state = phase.phase_states.get(member__user=secondary_user)
        Order.objects.create(phase_state=primary_phase_state, order_type="Move", source="lon", target="eng")
        Order.objects.create(phase_state=secondary_phase_state, order_type="Move", source="par", target="bur")
        url = reverse("order-list", args=[game.id, phase.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(connection.queries) == 3


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

        assert query_count == 8


class TestGetOptionsForOrder:

    @pytest.mark.django_db
    def test_no_source_returns_nation_provinces(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source=None, order_type=None, target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert "bud" in options
        assert "tri" in options
        assert len(options) == 2

    @pytest.mark.django_db
    def test_with_source_only_returns_order_types(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type=None, target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert "Hold" in options
        assert "Move" in options
        assert "Support" in options
        assert len(options) == 3

    @pytest.mark.django_db
    def test_with_source_and_move_order_type_returns_targets(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="Move", target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert "gal" in options
        assert "rum" in options
        assert "ser" in options
        assert "tri" in options
        assert "vie" in options
        assert len(options) == 5

    @pytest.mark.django_db
    def test_hold_order_with_all_fields_returns_empty_list(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="Hold", target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert options == []

    @pytest.mark.django_db
    def test_move_order_with_all_fields_returns_empty_list(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="Move", target="tri", aux=None)
        options = get_options_for_order(sample_options, order)
        assert options == []

    @pytest.mark.django_db
    def test_support_order_with_all_fields_returns_empty_list(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="Support", target="tri", aux="tri")
        options = get_options_for_order(sample_options, order)
        assert options == []

    @pytest.mark.django_db
    def test_invalid_source_raises_error(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="invalid", order_type=None, target=None, aux=None)
        with pytest.raises(ValueError, match="Source province invalid not found in options"):
            get_options_for_order(sample_options, order)

    @pytest.mark.django_db
    def test_invalid_order_type_raises_error(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="InvalidType", target=None, aux=None)
        with pytest.raises(ValueError, match="Order type InvalidType not found in options"):
            get_options_for_order(sample_options, order)

    @pytest.mark.django_db
    def test_invalid_target_raises_error(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="Move", target="invalid", aux=None)
        with pytest.raises(ValueError, match="Target province invalid not found in options"):
            get_options_for_order(sample_options, order)

    @pytest.mark.django_db
    def test_invalid_aux_raises_error(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="Support", target="tri", aux="invalid")
        with pytest.raises(ValueError, match="Auxiliary province invalid not found in options"):
            get_options_for_order(sample_options, order)

    @pytest.mark.django_db
    def test_nested_support_order_options(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="Support", target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert "sev" in options
        assert "tri" in options
        assert "vie" in options
        assert len(options) == 3

    @pytest.mark.django_db
    def test_support_order_target_selection_after_aux(self, sample_options, test_phase_state):
        order = Order(phase_state=test_phase_state, source="bud", order_type="Support", target=None, aux="vie")
        options = get_options_for_order(sample_options, order)
        assert "gal" in options
        assert "tri" in options
        assert "vie" in options
        assert len(options) == 3

    @pytest.mark.django_db
    def test_empty_options_structure(self, test_phase_state):
        empty_options = {}
        order = Order(phase_state=test_phase_state, source=None, order_type=None, target=None, aux=None)

        with pytest.raises(KeyError):
            get_options_for_order(empty_options, order)

    @pytest.mark.django_db
    def test_convoy_order_structure(self, sample_options, test_phase_state):
        sample_options["England"]["bud"]["Next"]["Convoy"] = {
            "Next": {
                "bud": {
                    "Next": {"sev": {"Next": {"rum": {"Next": {}, "Type": "Province"}}, "Type": "Province"}},
                    "Type": "SrcProvince",
                }
            },
            "Type": "OrderType",
        }
        order = Order(phase_state=test_phase_state, source="bud", order_type="Convoy", target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert "sev" in options
        assert len(options) == 1

    @pytest.mark.django_db
    def test_build_order_structure(self, sample_options, test_phase_state):
        sample_options["England"]["bud"]["Next"]["Build"] = {
            "Next": {
                "bud": {
                    "Next": {"Army": {"Next": {}, "Type": "UnitType"}, "Fleet": {"Next": {}, "Type": "UnitType"}},
                    "Type": "SrcProvince",
                }
            },
            "Type": "OrderType",
        }
        order = Order(phase_state=test_phase_state, source="bud", order_type="Build", target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert "Army" in options
        assert "Fleet" in options
        assert len(options) == 2

    @pytest.mark.django_db
    def test_disband_order_structure(self, sample_options, test_phase_state):
        sample_options["England"]["bud"]["Next"]["Disband"] = {
            "Next": {"bud": {"Next": {}, "Type": "SrcProvince"}},
            "Type": "OrderType",
        }
        order = Order(phase_state=test_phase_state, source="bud", order_type="Disband", target=None, aux=None)
        options = get_options_for_order(sample_options, order)
        assert options == []


class TestOrderComplete:

    @pytest.mark.django_db
    def test_hold_order_is_always_complete(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.HOLD, source="lon")
        assert order.complete is True

    @pytest.mark.django_db
    def test_disband_order_is_always_complete(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.DISBAND, source="lon")
        assert order.complete is True

    @pytest.mark.django_db
    def test_move_order_complete_when_target_set(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.MOVE, source="lon", target="eng")
        assert order.complete is True

    @pytest.mark.django_db
    def test_move_order_incomplete_when_target_none(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.MOVE, source="lon", target=None)
        assert order.complete is False

    @pytest.mark.django_db
    def test_move_order_complete_when_target_empty_string(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.MOVE, source="lon", target="")
        assert order.complete is True

    @pytest.mark.django_db
    def test_build_order_complete_when_unit_type_set(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.BUILD, source="lon", unit_type=UnitType.FLEET)
        assert order.complete is True

        order_army = Order(
            phase_state=test_phase_state, order_type=OrderType.BUILD, source="lon", unit_type=UnitType.ARMY
        )
        assert order_army.complete is True

    @pytest.mark.django_db
    def test_build_order_incomplete_when_unit_type_none(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.BUILD, source="lon", unit_type=None)
        assert order.complete is False

    @pytest.mark.django_db
    def test_build_order_complete_when_unit_type_empty_string(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.BUILD, source="lon", unit_type="")
        assert order.complete is True

    @pytest.mark.django_db
    def test_support_order_complete_when_target_and_aux_set(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.SUPPORT, source="lon", target="eng", aux="spa")
        assert order.complete is True

    @pytest.mark.django_db
    def test_support_order_incomplete_when_target_none(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.SUPPORT, source="lon", target=None, aux="spa")
        assert order.complete is False

    @pytest.mark.django_db
    def test_support_order_incomplete_when_aux_none(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.SUPPORT, source="lon", target="eng", aux=None)
        assert order.complete is False

    @pytest.mark.django_db
    def test_support_order_incomplete_when_both_target_and_aux_none(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.SUPPORT, source="lon", target=None, aux=None)
        assert order.complete is False

    @pytest.mark.django_db
    def test_convoy_order_complete_when_target_and_aux_set(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.CONVOY, source="eng", target="lon", aux="spa")
        assert order.complete is True

    @pytest.mark.django_db
    def test_convoy_order_incomplete_when_target_none(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.CONVOY, source="eng", target=None, aux="spa")
        assert order.complete is False

    @pytest.mark.django_db
    def test_convoy_order_incomplete_when_aux_none(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.CONVOY, source="eng", target="lon", aux=None)
        assert order.complete is False

    @pytest.mark.django_db
    def test_convoy_order_incomplete_when_both_target_and_aux_none(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=OrderType.CONVOY, source="eng", target=None, aux=None)
        assert order.complete is False

    @pytest.mark.django_db
    def test_order_complete_with_none_order_type(self, test_phase_state):
        order = Order(phase_state=test_phase_state, order_type=None, source="lon")
        assert order.complete is False
