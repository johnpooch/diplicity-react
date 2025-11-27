from adjudication.service import resolve
import json
import pytest
from django.db import IntegrityError, DatabaseError
from django.urls import reverse
from django.utils import timezone
from django.test.utils import override_settings
from django.db import connection
from datetime import timedelta
from unittest.mock import patch, Mock
from rest_framework import status
from common.constants import PhaseStatus, PhaseType, OrderType, UnitType, GameStatus
from game.models import Game
from .models import Phase, PhaseState
from .serializers import PhaseStateSerializer
from .utils import transform_options
from order.models import Order, OrderResolution
from supply_center.models import SupplyCenter
from unit.models import Unit


@pytest.mark.django_db
def test_confirm_phase_success(
    authenticated_client, active_game_with_phase_state, secondary_user, classical_france_nation
):
    # Add secondary user so that phase doesn't resolve
    secondary_member = active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)
    active_game_with_phase_state.current_phase.phase_states.create(member=secondary_member)

    url = reverse("game-confirm-phase", args=[active_game_with_phase_state.id])
    response = authenticated_client.put(url)
    assert response.status_code == status.HTTP_200_OK

    phase_states = active_game_with_phase_state.current_phase.phase_states.all()
    phase_state = phase_states.first()
    phase_state.refresh_from_db()
    assert phase_state.orders_confirmed


@pytest.mark.django_db
def test_confirm_phase_already_confirmed(authenticated_client, active_game_with_confirmed_phase_state):
    url = reverse("game-confirm-phase", args=[active_game_with_confirmed_phase_state.id])
    response = authenticated_client.put(url)
    assert response.status_code == status.HTTP_200_OK

    phase_state = active_game_with_confirmed_phase_state.current_phase.phase_states.first()
    assert not phase_state.orders_confirmed


@pytest.mark.django_db
def test_confirm_phase_game_not_active(authenticated_client, pending_game_created_by_primary_user):
    url = reverse("game-confirm-phase", args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_not_member(authenticated_client, active_game_created_by_secondary_user):
    url = reverse("game-confirm-phase", args=[active_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_eliminated(authenticated_client_for_secondary_user, active_game_with_eliminated_member):
    url = reverse("game-confirm-phase", args=[active_game_with_eliminated_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_kicked(authenticated_client_for_secondary_user, active_game_with_kicked_member):
    url = reverse("game-confirm-phase", args=[active_game_with_kicked_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_unauthenticated(unauthenticated_client, active_game_with_phase_state):
    url = reverse("game-confirm-phase", args=[active_game_with_phase_state.id])
    response = unauthenticated_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_list_orderable_provinces_success(authenticated_client, active_game_with_phase_options):
    url = reverse("phase-state-list", args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert "orderable_provinces" in response.data[0]


@pytest.mark.django_db
def test_list_orderable_provinces_sandbox_game(authenticated_client, sandbox_game_with_phase_options):
    url = reverse("phase-state-list", args=[sandbox_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 7


@pytest.mark.django_db
def test_list_orderable_provinces_not_member(authenticated_client, active_game_created_by_secondary_user):
    url = reverse("phase-state-list", args=[active_game_created_by_secondary_user.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_resolve_phases_success(authenticated_client):
    url = reverse("phase-resolve-all")
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert "resolved" in response.data
    assert "failed" in response.data


@pytest.mark.django_db
def test_phase_should_resolve_immediately_no_users_with_orders(active_game_with_phase_state):
    phase = active_game_with_phase_state.current_phase
    phase.options = {"England": {}}
    phase.save()
    assert phase.should_resolve_immediately


@pytest.mark.django_db
def test_phase_should_resolve_immediately_all_confirmed(
    active_game_with_phase_state, godip_options_england_london_hold
):
    phase = active_game_with_phase_state.current_phase
    phase.options = godip_options_england_london_hold
    phase.save()
    assert not phase.should_resolve_immediately
    phase_state = phase.phase_states.first()
    phase_state.orders_confirmed = True
    phase_state.save()
    phase.refresh_from_db()
    assert phase.should_resolve_immediately


@pytest.mark.django_db
def test_phase_should_not_resolve_immediately_partial_confirmation(
    active_game_with_phase_state, secondary_user, classical_france_nation, godip_options_england_france_both_hold
):
    phase = active_game_with_phase_state.current_phase
    secondary_member = active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)
    phase.phase_states.create(member=secondary_member)
    phase.options = godip_options_england_france_both_hold
    phase.save()
    first_phase_state = phase.phase_states.first()
    first_phase_state.orders_confirmed = True
    first_phase_state.save()
    phase.refresh_from_db()
    assert not phase.should_resolve_immediately


@pytest.mark.django_db
def test_nations_with_possible_orders_various_scenarios(
    godip_options_england_london_hold, godip_options_england_france_both_hold
):
    phase = Phase()
    phase.options = {}
    assert len(phase.nations_with_possible_orders) == 0
    phase.options = {"England": {}, "France": {}}
    assert len(phase.nations_with_possible_orders) == 0
    phase.options = godip_options_england_london_hold
    nations = phase.nations_with_possible_orders
    assert len(nations) == 1
    assert "England" in nations
    phase.options = godip_options_england_france_both_hold
    nations = phase.nations_with_possible_orders
    assert len(nations) == 2
    assert "England" in nations
    assert "France" in nations


@pytest.mark.django_db
def test_resolve_due_phases_with_scheduled_time(active_game_with_phase_state):
    phase = active_game_with_phase_state.current_phase
    past_time = timezone.now() - timedelta(hours=1)
    phase.scheduled_resolution = past_time
    phase.save()
    with patch.object(Phase.objects, "resolve") as mock_resolve:
        result = Phase.objects.resolve_due_phases()
        assert result["resolved"] == 1
        assert result["failed"] == 0
        mock_resolve.assert_called_once_with(phase)


@pytest.mark.django_db
def test_resolve_due_phases_with_immediate_resolution(active_game_with_phase_state):
    phase = active_game_with_phase_state.current_phase

    future_time = timezone.now() + timedelta(hours=24)
    phase.scheduled_resolution = future_time
    phase.options = {}
    phase.save()
    phase_state = phase.phase_states.first()
    phase_state.has_possible_orders = False
    phase_state.save()
    with patch.object(Phase.objects, "resolve") as mock_resolve:
        result = Phase.objects.resolve_due_phases()
        assert result["resolved"] == 1
        assert result["failed"] == 0
        mock_resolve.assert_called_once_with(phase)


@pytest.mark.django_db
def test_resolve_due_phases_no_resolution_needed(active_game_with_phase_state, godip_options_england_london_hold):
    phase = active_game_with_phase_state.current_phase

    future_time = timezone.now() + timedelta(hours=24)
    phase.scheduled_resolution = future_time
    phase.options = godip_options_england_london_hold
    phase.save()
    with patch.object(Phase.objects, "resolve") as mock_resolve:
        result = Phase.objects.resolve_due_phases()
        assert result["resolved"] == 0
        assert result["failed"] == 0
        mock_resolve.assert_not_called()


@pytest.mark.django_db
def test_resolve_due_phases_skips_sandbox_games(db, classical_variant, primary_user):
    from game.models import Game
    from common.constants import NationAssignment

    game = Game.objects.create_from_template(
        classical_variant,
        name="Sandbox Game",
        sandbox=True,
        private=True,
        nation_assignment=NationAssignment.ORDERED,
        movement_phase_duration=None,
    )
    for nation in classical_variant.nations.all():
        game.members.create(user=primary_user)
    game.start()

    phase = game.current_phase
    assert phase.scheduled_resolution is None
    assert phase.status == PhaseStatus.ACTIVE

    with patch.object(Phase.objects, "resolve") as mock_resolve:
        result = Phase.objects.resolve_due_phases()
        assert result["resolved"] == 0
        assert result["failed"] == 0
        mock_resolve.assert_not_called()


@pytest.mark.django_db
def test_sandbox_game_resolve_phase_success(authenticated_client, db, classical_variant, primary_user):
    from game.models import Game
    from common.constants import NationAssignment

    game = Game.objects.create_from_template(
        classical_variant,
        name="Sandbox Game",
        sandbox=True,
        private=True,
        nation_assignment=NationAssignment.ORDERED,
        movement_phase_duration=None,
    )
    for nation in classical_variant.nations.all():
        game.members.create(user=primary_user)
    game.start()

    url = reverse("game-resolve-phase", args=[game.id])
    with patch.object(Phase.objects, "resolve") as mock_resolve:
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_resolve.assert_called_once()


@pytest.mark.django_db
def test_sandbox_game_resolve_phase_unauthenticated(unauthenticated_client, db, classical_variant, primary_user):
    from game.models import Game
    from common.constants import NationAssignment

    game = Game.objects.create_from_template(
        classical_variant,
        name="Sandbox Game",
        sandbox=True,
        private=True,
        nation_assignment=NationAssignment.ORDERED,
        movement_phase_duration=None,
    )
    for nation in classical_variant.nations.all():
        game.members.create(user=primary_user)
    game.start()

    url = reverse("game-resolve-phase", args=[game.id])
    response = unauthenticated_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_regular_game_cannot_use_sandbox_resolve(authenticated_client, active_game_with_phase_state):
    url = reverse("game-resolve-phase", args=[active_game_with_phase_state.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "only available for sandbox games" in str(response.data).lower()


@pytest.mark.django_db
def test_sandbox_game_resolve_phase_non_member(
    authenticated_client_for_secondary_user, db, classical_variant, primary_user
):
    from game.models import Game
    from common.constants import NationAssignment

    game = Game.objects.create_from_template(
        classical_variant,
        name="Sandbox Game",
        sandbox=True,
        private=True,
        nation_assignment=NationAssignment.ORDERED,
        movement_phase_duration=None,
    )
    for nation in classical_variant.nations.all():
        game.members.create(user=primary_user)
    game.start()

    url = reverse("game-resolve-phase", args=[game.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAdjustmentPhaseOrderLimits:

    @pytest.mark.django_db
    def test_max_allowed_orders_non_adjustment_phase(self, active_game_with_phase_state):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.MOVEMENT
        phase.save()

        phase_state = phase.phase_states.first()
        assert phase_state.max_allowed_adjustment_orders() == float("inf")

    @pytest.mark.django_db
    def test_max_allowed_orders_can_build_surplus(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.save()

        # Nation has 2 supply centers but only 1 unit (can build 1)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()
        assert phase_state.max_allowed_adjustment_orders() == 1

    @pytest.mark.django_db
    def test_max_allowed_orders_must_disband_surplus(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.save()

        # Nation has 1 supply center but 2 units (must disband 1)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Army", nation=classical_england_nation, province=classical_paris_province)

        phase_state = phase.phase_states.first()
        assert phase_state.max_allowed_adjustment_orders() == 1

    @pytest.mark.django_db
    def test_max_allowed_orders_balanced(
        self, active_game_with_phase_state, classical_england_nation, classical_london_province
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.save()

        # Nation has 1 supply center and 1 unit (balanced)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()
        assert phase_state.max_allowed_adjustment_orders() == 0

    @pytest.mark.django_db
    def test_max_allowed_orders_no_supply_centers_no_units(self, active_game_with_phase_state):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.save()

        # Nation has 0 supply centers and 0 units (balanced)
        phase_state = phase.phase_states.first()
        assert phase_state.max_allowed_adjustment_orders() == 0

    @pytest.mark.django_db
    def test_orderable_provinces_movement_phase_no_limit(self, active_game_with_phase_state):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.MOVEMENT
        phase.options = {"England": {"lon": {}, "par": {}}}
        phase.save()

        phase_state = phase.phase_states.first()
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 2

    @pytest.mark.django_db
    def test_orderable_provinces_adjustment_under_limit(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {"England": {"lon": {}, "par": {}}}
        phase.save()

        # Nation can build 1 order (2 supply centers, 1 unit)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 2  # Both provinces available

    @pytest.mark.django_db
    def test_orderable_provinces_adjustment_at_limit_no_orders(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {"England": {"lon": {}, "par": {}}}
        phase.save()

        # Nation can build 1 order (2 supply centers, 1 unit)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        # Create 1 order (at limit)
        phase_state = phase.phase_states.first()
        Order.objects.create(phase_state=phase_state, source=classical_london_province, order_type=OrderType.BUILD)

        orderable = phase_state.orderable_provinces
        assert orderable.count() == 1  # Only province with existing order
        assert orderable.first().province_id == "lon"

    @pytest.mark.django_db
    def test_orderable_provinces_adjustment_at_limit_with_order(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {"England": {"lon": {}, "par": {}}}
        phase.save()

        # Nation has balanced supply centers and units (0 orders allowed)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 0  # No provinces available (at limit with 0 allowed)

    @pytest.mark.django_db
    def test_orderable_provinces_adjustment_balanced_no_orders_allowed(
        self, active_game_with_phase_state, classical_england_nation, classical_london_province
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {"England": {"lon": {}, "par": {}}}
        phase.save()

        # Nation has balanced supply centers and units (0 orders allowed)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 0

    @pytest.mark.django_db
    def test_orderable_provinces_can_edit_existing_orders_at_limit(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {"England": {"lon": {}, "par": {}}}
        phase.save()

        # Nation can build 1 order
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        phase_state = phase.phase_states.first()

        # Before creating order: can see all provinces
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 2

        # Create order for london
        Order.objects.create(phase_state=phase_state, source=classical_london_province, order_type=OrderType.BUILD)

        # After creating order (at limit): can only see provinces with existing orders
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 1
        assert orderable.first().province_id == "lon"

        # Delete the order
        Order.objects.filter(phase_state=phase_state).delete()

        # After deleting: can see all provinces again
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 2

    @pytest.mark.django_db
    def test_large_surplus_multiple_builds_allowed(
        self,
        active_game_with_phase_state,
        classical_england_nation,
        classical_london_province,
        classical_paris_province,
        classical_edinburgh_province,
    ):
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.options = {"England": {"lon": {}, "par": {}, "edi": {}}}
        phase.save()

        # Nation has 3 supply centers but 0 units (can build 3)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_paris_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

        phase_state = phase.phase_states.first()
        assert phase_state.max_allowed_adjustment_orders() == 3

        # All provinces should be orderable initially
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 3

        # Create 2 orders
        Order.objects.create(phase_state=phase_state, source=classical_london_province, order_type=OrderType.BUILD)
        Order.objects.create(phase_state=phase_state, source=classical_paris_province, order_type=OrderType.BUILD)

        # Still under limit, should see all provinces
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 3

        # Create 3rd order (at limit)
        Order.objects.create(phase_state=phase_state, source=classical_edinburgh_province, order_type=OrderType.BUILD)

        # At limit, should only see provinces with orders
        orderable = phase_state.orderable_provinces
        assert orderable.count() == 3  # All have orders
        assert set(p.province_id for p in orderable) == {"lon", "par", "edi"}


class TestOptionsTransformation:

    @pytest.mark.django_db
    def test_transform_simple_hold_order(self):
        raw_options = {
            "England": {
                "lon": {
                    "Next": {"Hold": {"Next": {"lon": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"}},
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"England": {"lon": {"Hold": {}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_simple_move_order(self):
        raw_options = {
            "England": {
                "lon": {
                    "Next": {
                        "Move": {
                            "Next": {
                                "lon": {
                                    "Next": {
                                        "eng": {"Next": {}, "Type": "Province"},
                                        "nth": {"Next": {}, "Type": "Province"},
                                        "wal": {"Next": {}, "Type": "Province"},
                                    },
                                    "Type": "SrcProvince",
                                }
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"England": {"lon": {"Move": {"eng": {}, "nth": {}, "wal": {}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_simple_support_order(self):
        raw_options = {
            "England": {
                "lon": {
                    "Next": {
                        "Support": {
                            "Next": {
                                "lon": {
                                    "Next": {
                                        "wal": {"Next": {"yor": {"Next": {}, "Type": "Province"}}, "Type": "Province"},
                                        "yor": {"Next": {"wal": {"Next": {}, "Type": "Province"}}, "Type": "Province"},
                                    },
                                    "Type": "SrcProvince",
                                }
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"England": {"lon": {"Support": {"wal": {"yor": {}}, "yor": {"wal": {}}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_simple_convoy_order(self):
        raw_options = {
            "England": {
                "nth": {
                    "Next": {
                        "Convoy": {
                            "Next": {
                                "nth": {
                                    "Next": {
                                        "yor": {
                                            "Next": {
                                                "bel": {"Next": {}, "Type": "Province"},
                                                "hol": {"Next": {}, "Type": "Province"},
                                            },
                                            "Type": "Province",
                                        }
                                    },
                                    "Type": "SrcProvince",
                                }
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"England": {"nth": {"Convoy": {"yor": {"bel": {}, "hol": {}}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_army_move_to_named_coast_province(self):
        raw_options = {
            "France": {
                "mar": {
                    "Next": {
                        "Move": {
                            "Next": {
                                "mar": {
                                    "Next": {
                                        "bur": {"Next": {}, "Type": "Province"},
                                        "gas": {"Next": {}, "Type": "Province"},
                                        "spa": {"Next": {}, "Type": "Province"},
                                    },
                                    "Type": "SrcProvince",
                                }
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"France": {"mar": {"Move": {"bur": {}, "gas": {}, "spa": {}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_army_move_from_named_coast_province(self):
        raw_options = {
            "France": {
                "spa": {
                    "Next": {
                        "Hold": {"Next": {"spa": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"},
                        "Move": {
                            "Next": {
                                "spa": {
                                    "Next": {
                                        "bre": {"Next": {}, "Type": "Province"},
                                        "gas": {"Next": {}, "Type": "Province"},
                                        "mar": {"Next": {}, "Type": "Province"},
                                        "por": {"Next": {}, "Type": "Province"},
                                    },
                                    "Type": "SrcProvince",
                                }
                            },
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"France": {"spa": {"Hold": {}, "Move": {"bre": {}, "gas": {}, "mar": {}, "por": {}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_fleet_move_from_named_coast_province(self):
        raw_options = {
            "Russia": {
                "stp": {
                    "Next": {
                        "Hold": {"Next": {"stp/sc": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"},
                        "Move": {
                            "Next": {
                                "stp/sc": {
                                    "Next": {
                                        "bot": {"Next": {}, "Type": "Province"},
                                        "fin": {"Next": {}, "Type": "Province"},
                                        "lvn": {"Next": {}, "Type": "Province"},
                                    },
                                    "Type": "SrcProvince",
                                }
                            },
                            "Type": "OrderType",
                        },
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"Russia": {"stp": {"Hold": {}, "Move": {"bot": {}, "fin": {}, "lvn": {}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_fleet_move_to_named_coast_province(self):
        raw_options = {
            "France": {
                "mid": {
                    "Next": {
                        "Move": {
                            "Next": {
                                "mid": {
                                    "Next": {
                                        "bre": {"Next": {}, "Type": "Province"},
                                        "eng": {"Next": {}, "Type": "Province"},
                                        "spa/nc": {"Next": {}, "Type": "Province"},
                                        "spa/sc": {"Next": {}, "Type": "Province"},
                                    },
                                    "Type": "SrcProvince",
                                }
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"France": {"mid": {"Move": {"bre": {}, "eng": {}, "spa": {"spa/nc": {}, "spa/sc": {}}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_fleet_move_to_single_named_coast(self):
        raw_options = {
            "Russia": {
                "bot": {
                    "Next": {
                        "Move": {
                            "Next": {
                                "bot": {
                                    "Next": {
                                        "bal": {"Next": {}, "Type": "Province"},
                                        "fin": {"Next": {}, "Type": "Province"},
                                        "stp/sc": {"Next": {}, "Type": "Province"},
                                    },
                                    "Type": "SrcProvince",
                                }
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"Russia": {"bot": {"Move": {"bal": {}, "fin": {}, "stp": {"stp/sc": {}}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_simple_build_army(self):
        raw_options = {
            "Germany": {
                "mun": {
                    "Next": {
                        "Build": {
                            "Next": {
                                "Army": {"Next": {"mun": {"Next": {}, "Type": "SrcProvince"}}, "Type": "UnitType"}
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"Germany": {"mun": {"Build": {"Army": {}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_coastal_build_army_and_fleet(self):
        raw_options = {
            "France": {
                "bre": {
                    "Next": {
                        "Build": {
                            "Next": {
                                "Army": {"Next": {"bre": {"Next": {}, "Type": "SrcProvince"}}, "Type": "UnitType"},
                                "Fleet": {"Next": {"bre": {"Next": {}, "Type": "SrcProvince"}}, "Type": "UnitType"},
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                }
            }
        }

        result = transform_options(raw_options)

        expected = {"France": {"bre": {"Build": {"Army": {}, "Fleet": {}}}}}

        assert result == expected

    @pytest.mark.django_db
    def test_transform_build_with_named_coasts(self):
        raw_options = {
            "Russia": {
                "stp/nc": {
                    "Next": {
                        "Build": {
                            "Next": {
                                "Army": {"Next": {"stp": {"Next": {}, "Type": "SrcProvince"}}, "Type": "UnitType"},
                                "Fleet": {"Next": {"stp/nc": {"Next": {}, "Type": "SrcProvince"}}, "Type": "UnitType"},
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                },
                "stp/sc": {
                    "Next": {
                        "Build": {
                            "Next": {
                                "Army": {"Next": {"stp": {"Next": {}, "Type": "SrcProvince"}}, "Type": "UnitType"},
                                "Fleet": {"Next": {"stp/sc": {"Next": {}, "Type": "SrcProvince"}}, "Type": "UnitType"},
                            },
                            "Type": "OrderType",
                        }
                    },
                    "Type": "Province",
                },
            }
        }

        result = transform_options(raw_options)

        expected = {"Russia": {"stp": {"Build": {"Army": {}, "Fleet": {"stp/nc": {}, "stp/sc": {}}}}}}

        assert result == expected


class TestCreateFromAdjudicationData:

    @pytest.mark.django_db
    def test_create_from_adjudication_data_basic(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        initial_phase_count = Phase.objects.count()

        new_phase = Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        assert Phase.objects.count() == initial_phase_count + 1
        assert new_phase.season == "Spring"
        assert new_phase.year == 1901
        assert new_phase.type == "Retreat"
        assert new_phase.ordinal == phase.ordinal + 1
        assert new_phase.status == PhaseStatus.ACTIVE
        assert new_phase.game == phase.game
        assert new_phase.variant == phase.variant

        assert new_phase.units.count() == 6
        assert new_phase.supply_centers.count() == 6

        italy_units = new_phase.units.filter(nation__name="Italy")
        assert italy_units.count() == 3

        germany_units = new_phase.units.filter(nation__name="Germany")
        assert germany_units.count() == 3

        ven_unit = new_phase.units.get(province__province_id="ven")
        assert ven_unit.type == UnitType.ARMY
        assert ven_unit.nation.name == "Italy"
        assert not ven_unit.dislodged
        assert ven_unit.dislodged_by is None

    @pytest.mark.django_db
    def test_create_from_adjudication_data_with_dislodged_unit(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_with_dislodged_unit,
    ):
        phase = italy_vs_germany_phase_with_orders

        new_phase = Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_with_dislodged_unit)

        assert new_phase.units.count() == 4

        dislodged_unit = new_phase.units.get(province__province_id="kie", nation__name="Germany")
        assert dislodged_unit.dislodged
        assert dislodged_unit.dislodged_by is not None

        dislodging_unit = phase.units.get(province__province_id="ven")
        assert dislodged_unit.dislodged_by == dislodging_unit

        attacker_unit = new_phase.units.get(province__province_id="kie", nation__name="Italy")
        assert not attacker_unit.dislodged
        assert attacker_unit.dislodged_by is None

    @pytest.mark.django_db
    def test_create_from_adjudication_data_marks_previous_phase_completed(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        assert phase.status == PhaseStatus.ACTIVE

        Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.COMPLETED

    @pytest.mark.django_db
    def test_create_from_adjudication_data_creates_phase_states(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        member_count = phase.game.members.count()

        new_phase = Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        assert new_phase.phase_states.count() == member_count
        assert new_phase.phase_states.count() == 2

        for phase_state in new_phase.phase_states.all():
            assert phase_state.orders_confirmed is False
            assert phase_state.eliminated is False

    @pytest.mark.django_db
    def test_create_from_adjudication_data_scheduled_resolution_time(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        duration_seconds = phase.game.movement_phase_duration_seconds

        new_phase = Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        assert new_phase.scheduled_resolution is not None

        time_diff = (new_phase.scheduled_resolution - timezone.now()).total_seconds()
        assert abs(time_diff - duration_seconds) < 2

    @pytest.mark.django_db
    def test_create_from_adjudication_data_creates_order_resolutions(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        orders_count = len(phase.all_orders)

        Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        resolved_orders = [order for order in phase.all_orders if hasattr(order, "resolution")]
        assert len(resolved_orders) == orders_count


class TestCreateFromAdjudicationDataPerformance:

    @pytest.mark.django_db
    def test_create_from_adjudication_data_query_count_with_small_game(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = Phase.objects.with_adjudication_data().get(pk=italy_vs_germany_phase_with_orders.pk)

        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        query_count = len(connection.queries)

        assert query_count == 12

    @pytest.mark.django_db
    def test_create_from_adjudication_data_query_count_with_full_game(
        self,
        classical_variant,
        primary_user,
        classical_england_nation,
        classical_france_nation,
        classical_germany_nation,
        classical_italy_nation,
        classical_austria_nation,
        classical_russia_nation,
        classical_turkey_nation,
        classical_london_province,
        classical_paris_province,
    ):
        from game.models import Game
        from province.models import Province

        game = Game.objects.create(
            name="Full Classical Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )

        nations = [
            classical_england_nation,
            classical_france_nation,
            classical_germany_nation,
            classical_italy_nation,
            classical_austria_nation,
            classical_russia_nation,
            classical_turkey_nation,
        ]

        for nation in nations:
            game.members.create(user=primary_user, nation=nation)

        berlin = Province.objects.get(province_id="ber", variant=classical_variant)
        rome = Province.objects.get(province_id="rom", variant=classical_variant)
        vienna = Province.objects.get(province_id="vie", variant=classical_variant)
        moscow = Province.objects.get(province_id="mos", variant=classical_variant)
        constantinople = Province.objects.get(province_id="con", variant=classical_variant)

        phase = game.phases.create(
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
            scheduled_resolution=timezone.now() - timedelta(hours=1),
            options={},
        )

        supply_centers_data = [
            (classical_london_province, classical_england_nation),
            (classical_paris_province, classical_france_nation),
            (berlin, classical_germany_nation),
            (rome, classical_italy_nation),
            (vienna, classical_austria_nation),
            (moscow, classical_russia_nation),
            (constantinople, classical_turkey_nation),
        ]

        for province, nation in supply_centers_data:
            phase.supply_centers.create(province=province, nation=nation)

        units_data = [
            (classical_london_province, classical_england_nation, UnitType.FLEET),
            (classical_paris_province, classical_france_nation, UnitType.ARMY),
            (berlin, classical_germany_nation, UnitType.ARMY),
            (rome, classical_italy_nation, UnitType.FLEET),
            (vienna, classical_austria_nation, UnitType.ARMY),
            (moscow, classical_russia_nation, UnitType.ARMY),
            (constantinople, classical_turkey_nation, UnitType.FLEET),
        ]

        for province, nation, unit_type in units_data:
            phase.units.create(province=province, nation=nation, type=unit_type)

        for member in game.members.all():
            phase_state = phase.phase_states.create(
                member=member,
                has_possible_orders=True,
            )
            phase_state.orders.create(
                source=supply_centers_data[nations.index(member.nation)][0],
                order_type=OrderType.HOLD,
            )

        # Create mock adjudication data for full game
        mock_adjudication_data = {
            "season": "Spring",
            "year": 1901,
            "type": "Retreat",
            "options": {},
            "supply_centers": [{"province": sc[0].province_id, "nation": sc[1].name} for sc in supply_centers_data],
            "units": [
                {"province": u[0].province_id, "nation": u[1].name, "type": u[2], "dislodged_by": None}
                for u in units_data
            ],
            "resolutions": [{"province": sc[0].province_id, "result": "OK", "by": None} for sc in supply_centers_data],
        }

        phase = Phase.objects.with_adjudication_data().get(pk=phase.pk)

        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data)

        query_count = len(connection.queries)

        assert query_count == 12


class TestPhaseReversion:

    @pytest.mark.django_db
    def test_revert_to_phase_success(self, game_with_three_phases):
        game = game_with_three_phases
        phase1 = game.phases.get(ordinal=1)

        initial_phase_count = game.phases.count()
        assert initial_phase_count == 3

        phase1.revert_to_this_phase()

        assert game.phases.count() == 1
        assert not game.phases.filter(ordinal=2).exists()
        assert not game.phases.filter(ordinal=3).exists()

        phase1.refresh_from_db()
        assert phase1.status == PhaseStatus.ACTIVE
        assert phase1.scheduled_resolution is not None
        assert phase1.scheduled_resolution > timezone.now()

        for phase_state in phase1.phase_states.all():
            assert phase_state.orders_confirmed is False

        assert phase1.phase_states.first().orders.count() == 0

    @pytest.mark.django_db
    def test_revert_to_phase_deletes_related_objects(self, game_with_three_phases):
        game = game_with_three_phases
        phase1 = game.phases.get(ordinal=1)
        phase2 = game.phases.get(ordinal=2)
        phase3 = game.phases.get(ordinal=3)

        phase1_units_count = phase1.units.count()
        phase1_supply_centers_count = phase1.supply_centers.count()
        phase2_units_count = phase2.units.count()
        phase3_units_count = phase3.units.count()

        assert phase1_units_count > 0
        assert phase2_units_count > 0
        assert phase3_units_count > 0

        phase1.revert_to_this_phase()

        phase1.refresh_from_db()
        assert phase1.units.count() == phase1_units_count
        assert phase1.supply_centers.count() == phase1_supply_centers_count

        assert not Phase.objects.filter(id=phase2.id).exists()
        assert not Phase.objects.filter(id=phase3.id).exists()

    @pytest.mark.django_db
    def test_revert_to_phase_multiple_later_phases(
        self,
        game_with_three_phases,
        italy_vs_germany_variant,
        italy_vs_germany_italy_nation,
        italy_vs_germany_venice_province,
    ):
        game = game_with_three_phases

        phase4 = Phase.objects.create(
            game=game,
            variant=italy_vs_germany_variant,
            season="Fall",
            year=1902,
            type="Movement",
            ordinal=4,
            status=PhaseStatus.ACTIVE,
        )
        phase4.units.create(
            province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
        )

        assert game.phases.count() == 4

        phase2 = game.phases.get(ordinal=2)
        phase2.revert_to_this_phase()

        assert game.phases.count() == 2
        assert game.phases.filter(ordinal=1).exists()
        assert game.phases.filter(ordinal=2).exists()
        assert not game.phases.filter(ordinal=3).exists()
        assert not game.phases.filter(ordinal=4).exists()

    @pytest.mark.django_db
    def test_revert_to_last_phase_no_deletion(self, game_with_three_phases):
        game = game_with_three_phases
        phase3 = game.phases.get(ordinal=3)

        initial_phase_count = game.phases.count()
        phase3_orders_count = Order.objects.filter(phase_state__phase=phase3).count()
        assert phase3_orders_count > 0

        phase3.revert_to_this_phase()

        assert game.phases.count() == initial_phase_count

        phase3.refresh_from_db()
        assert phase3.status == PhaseStatus.ACTIVE

        assert Order.objects.filter(phase_state__phase=phase3).count() == 0

    @pytest.mark.django_db
    def test_revert_to_phase_recalculates_scheduled_resolution(self, game_with_three_phases):
        game = game_with_three_phases
        phase1 = game.phases.get(ordinal=1)

        duration_seconds = game.movement_phase_duration_seconds
        before_revert = timezone.now()

        phase1.revert_to_this_phase()

        phase1.refresh_from_db()
        assert phase1.scheduled_resolution is not None

        expected_resolution = before_revert + timedelta(seconds=duration_seconds)
        time_diff = abs((phase1.scheduled_resolution - expected_resolution).total_seconds())
        assert time_diff < 2

    @pytest.mark.django_db
    def test_revert_to_phase_clears_orders(self, game_with_three_phases):
        game = game_with_three_phases
        phase1 = game.phases.get(ordinal=1)

        phase1.status = PhaseStatus.ACTIVE
        phase1.save()

        phase_state = phase1.phase_states.first()

        initial_orders_count = phase_state.orders.count()
        assert initial_orders_count > 0

        phase1.revert_to_this_phase()

        assert phase_state.orders.count() == 0

    @pytest.mark.django_db
    def test_revert_to_phase_resets_phase_state_flags(self, game_with_three_phases):
        game = game_with_three_phases
        phase3 = game.phases.get(ordinal=3)

        phase_state_confirmed = phase3.phase_states.filter(orders_confirmed=True).first()
        assert phase_state_confirmed is not None

        phase3.revert_to_this_phase()

        for phase_state in phase3.phase_states.all():
            phase_state.refresh_from_db()
            assert phase_state.orders_confirmed is False

    @pytest.mark.django_db
    def test_revert_to_phase_ended_game_raises_error(
        self,
        game_with_three_phases,
    ):
        game = game_with_three_phases
        game.status = GameStatus.COMPLETED
        game.save()

        phase1 = game.phases.get(ordinal=1)

        with pytest.raises(ValueError, match="Cannot revert phases in an ended game"):
            phase1.revert_to_this_phase()

        assert game.phases.count() == 3

    @pytest.mark.django_db
    def test_revert_to_phase_with_order_resolutions(self, game_with_three_phases):
        game = game_with_three_phases
        phase1 = game.phases.get(ordinal=1)
        phase2 = game.phases.get(ordinal=2)

        order_resolutions_phase2 = [order.resolution for order in phase2.all_orders if hasattr(order, "resolution")]
        assert len(order_resolutions_phase2) > 0

        phase1.revert_to_this_phase()

        from order.models import OrderResolution

        for resolution in order_resolutions_phase2:
            assert not OrderResolution.objects.filter(id=resolution.id).exists()

    @pytest.mark.django_db
    def test_revert_to_completed_phase_makes_active(self, game_with_three_phases):
        game = game_with_three_phases
        phase1 = game.phases.get(ordinal=1)

        assert phase1.status == PhaseStatus.COMPLETED

        phase1.revert_to_this_phase()

        phase1.refresh_from_db()
        assert phase1.status == PhaseStatus.ACTIVE


class TestPhaseRetrieveView:

    @pytest.mark.django_db
    def test_retrieve_phase_success(self, authenticated_client, active_game_with_phase_state):
        game = active_game_with_phase_state
        phase = game.current_phase
        url = reverse("phase-retrieve", args=[game.id, phase.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == phase.id
        assert response.data["ordinal"] == phase.ordinal
        assert response.data["season"] == phase.season
        assert response.data["year"] == phase.year
        assert response.data["type"] == phase.type
        assert response.data["status"] == phase.status

    @pytest.mark.django_db
    def test_retrieve_phase_unauthenticated(self, unauthenticated_client, active_game_with_phase_state):
        game = active_game_with_phase_state
        phase = game.current_phase
        url = reverse("phase-retrieve", args=[game.id, phase.id])
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_retrieve_phase_not_found(self, authenticated_client, active_game_with_phase_state):
        game = active_game_with_phase_state
        url = reverse("phase-retrieve", args=[game.id, 99999])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_retrieve_phase_response_structure(self, authenticated_client, active_game_with_phase_state):
        game = active_game_with_phase_state
        phase = game.current_phase
        url = reverse("phase-retrieve", args=[game.id, phase.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        required_fields = [
            "id",
            "ordinal",
            "season",
            "year",
            "name",
            "type",
            "remaining_time",
            "scheduled_resolution",
            "status",
            "units",
            "supply_centers",
        ]
        for field in required_fields:
            assert field in response.data

        assert isinstance(response.data["units"], list)
        assert isinstance(response.data["supply_centers"], list)

    @pytest.mark.django_db
    def test_retrieve_phase_with_units_and_supply_centers(
        self, authenticated_client, active_game_with_phase_state, classical_england_nation, classical_london_province
    ):
        game = active_game_with_phase_state
        phase = game.current_phase

        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)

        url = reverse("phase-retrieve", args=[game.id, phase.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert len(response.data["units"]) > 0
        assert len(response.data["supply_centers"]) > 0

        unit = response.data["units"][0]
        assert "type" in unit
        assert "nation" in unit
        assert "province" in unit

        supply_center = response.data["supply_centers"][0]
        assert "nation" in supply_center
        assert "province" in supply_center


class TestPhaseRetrieveViewQueryPerformance:

    @pytest.mark.django_db
    def test_retrieve_phase_query_count(
        self,
        authenticated_client,
        active_game_with_phase_state,
        classical_england_nation,
        classical_france_nation,
        classical_london_province,
        classical_paris_province,
        classical_edinburgh_province,
    ):
        game = active_game_with_phase_state
        phase = game.current_phase

        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Army", nation=classical_france_nation, province=classical_paris_province)
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)

        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_france_nation, province=classical_paris_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

        url = reverse("phase-retrieve", args=[game.id, phase.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)

        assert query_count == 9


class TestGetPhasesToResolvePerformance:

    @pytest.mark.django_db
    def test_get_phases_to_resolve_query_count(
        self,
        classical_variant,
        primary_user,
        secondary_user,
        classical_england_nation,
        classical_france_nation,
        godip_options_england_london_hold,
    ):
        for i in range(10):
            game = Game.objects.create(
                name=f"Game {i}",
                variant=classical_variant,
                status=GameStatus.ACTIVE,
            )
            game.members.create(user=primary_user, nation=classical_england_nation)
            game.members.create(user=secondary_user, nation=classical_france_nation)

            previous_phase = game.phases.create(
                variant=game.variant,
                season="Spring",
                year=1901,
                type="Movement",
                status=PhaseStatus.COMPLETED,
                ordinal=1,
                scheduled_resolution=timezone.now() - timedelta(hours=1),
                options=godip_options_england_london_hold,
            )

            for member in game.members.all():
                previous_phase.phase_states.create(member=member)

            active_phase = game.phases.create(
                variant=game.variant,
                season="Spring",
                year=1901,
                type="Retreat",
                status=PhaseStatus.ACTIVE,
                ordinal=2,
                scheduled_resolution=timezone.now() - timedelta(hours=1),
                options=godip_options_england_london_hold,
            )

            for member in game.members.all():
                active_phase.phase_states.create(member=member)

        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            phases_to_resolve = Phase.objects.get_phases_to_resolve()

        query_count = len(connection.queries)

        assert query_count == 7


class TestResolveTransactionSafety:

    @pytest.mark.django_db
    def test_resolve_rollback_on_database_error(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        initial_phase_count = Phase.objects.count()
        initial_phase_status = phase.status

        with patch("phase.models.resolve") as mock_resolve:
            mock_resolve.return_value = mock_adjudication_data_basic

            original_save = phase.save

            def fail_on_save(*args, **kwargs):
                raise IntegrityError("Simulated database integrity error")

            with patch.object(phase, "save", side_effect=fail_on_save):
                with pytest.raises(IntegrityError, match="Simulated database integrity error"):
                    Phase.objects.resolve(phase)

        assert Phase.objects.count() == initial_phase_count
        phase.refresh_from_db()
        assert phase.status == initial_phase_status
        assert phase.status == PhaseStatus.ACTIVE

        from order.models import OrderResolution

        resolution_count = OrderResolution.objects.filter(order__phase_state__phase=phase).count()
        assert resolution_count == 0

    @pytest.mark.django_db
    def test_resolve_rollback_after_phase_created(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        game = phase.game
        initial_phase_count = Phase.objects.count()
        initial_active_phases = Phase.objects.filter(status=PhaseStatus.ACTIVE).count()

        with patch("phase.models.resolve") as mock_resolve:
            mock_resolve.return_value = mock_adjudication_data_basic

            original_create_from_adj = Phase.objects.create_from_adjudication_data

            def create_then_fail(*args, **kwargs):
                result = original_create_from_adj(*args, **kwargs)
                raise DatabaseError("Simulated database error after creation")

            with patch.object(Phase.objects, "create_from_adjudication_data", side_effect=create_then_fail):
                with pytest.raises(DatabaseError, match="Simulated database error after creation"):
                    Phase.objects.resolve(phase)

        assert Phase.objects.count() == initial_phase_count

        active_phases = Phase.objects.filter(status=PhaseStatus.ACTIVE).count()
        assert active_phases == initial_active_phases

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_resolve_rollback_during_supply_center_creation(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):

        phase = italy_vs_germany_phase_with_orders
        initial_phase_count = Phase.objects.count()
        initial_sc_count = SupplyCenter.objects.count()

        with patch("phase.models.resolve") as mock_resolve:
            mock_resolve.return_value = mock_adjudication_data_basic

            original_create_from_adj = Phase.objects.create_from_adjudication_data

            def failing_create(*args, **kwargs):
                phase_obj = args[0]
                adj_data = args[1]

                new_phase = Phase.objects.create(
                    game=phase_obj.game,
                    variant=phase_obj.variant,
                    ordinal=phase_obj.ordinal + 1,
                    season=adj_data["season"],
                    year=adj_data["year"],
                    type=adj_data["type"],
                    options=adj_data["options"],
                    status=PhaseStatus.ACTIVE,
                    scheduled_resolution=None,
                )

                raise Exception("Simulated failure during supply center creation")

            with patch.object(Phase.objects, "create_from_adjudication_data", side_effect=failing_create):
                with pytest.raises(Exception, match="Simulated failure during supply center creation"):
                    Phase.objects.resolve(phase)

        assert Phase.objects.count() == initial_phase_count
        assert SupplyCenter.objects.count() == initial_sc_count

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_resolve_rollback_during_unit_creation(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):

        phase = italy_vs_germany_phase_with_orders
        initial_phase_count = Phase.objects.count()
        initial_unit_count = Unit.objects.count()

        with patch("phase.models.resolve") as mock_resolve:
            mock_resolve.return_value = mock_adjudication_data_basic

            original_method = Phase.objects.create_from_adjudication_data

            call_count = [0]

            def failing_on_units(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    original_method(*args, **kwargs)
                    raise Exception("Simulated failure after phase creation")
                return original_method(*args, **kwargs)

            with patch.object(Phase.objects, "create_from_adjudication_data", side_effect=failing_on_units):
                with pytest.raises(Exception, match="Simulated failure after phase creation"):
                    Phase.objects.resolve(phase)

        assert Phase.objects.count() == initial_phase_count
        assert Unit.objects.count() == initial_unit_count

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_resolve_no_partial_data_on_failure(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders

        initial_counts = {
            "phases": Phase.objects.count(),
            "order_resolutions": OrderResolution.objects.count(),
            "supply_centers": SupplyCenter.objects.count(),
            "units": Unit.objects.count(),
            "phase_states": PhaseState.objects.count(),
        }

        with patch("phase.models.resolve") as mock_resolve:
            mock_resolve.return_value = mock_adjudication_data_basic

            original_method = Phase.objects.create_from_adjudication_data

            def fail_mid_process(*args, **kwargs):
                original_method(*args, **kwargs)
                raise Exception("Simulated mid-process failure")

            with patch.object(Phase.objects, "create_from_adjudication_data", side_effect=fail_mid_process):
                with pytest.raises(Exception, match="Simulated mid-process failure"):
                    Phase.objects.resolve(phase)

        assert Phase.objects.count() == initial_counts["phases"]
        assert OrderResolution.objects.count() == initial_counts["order_resolutions"]
        assert SupplyCenter.objects.count() == initial_counts["supply_centers"]
        assert Unit.objects.count() == initial_counts["units"]
        assert PhaseState.objects.count() == initial_counts["phase_states"]

    @pytest.mark.django_db
    def test_resolve_commits_all_data_on_success(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        orders_count = len(phase.all_orders)
        member_count = phase.game.members.count()

        initial_counts = {
            "phases": Phase.objects.count(),
            "order_resolutions": OrderResolution.objects.count(),
            "supply_centers": SupplyCenter.objects.count(),
            "units": Unit.objects.count(),
            "phase_states": PhaseState.objects.count(),
        }

        with patch("phase.models.resolve") as mock_resolve:
            mock_resolve.return_value = mock_adjudication_data_basic

            Phase.objects.resolve(phase)

        assert Phase.objects.count() == initial_counts["phases"] + 1

        assert OrderResolution.objects.count() == initial_counts["order_resolutions"] + orders_count

        new_phase = phase.game.phases.last()
        assert new_phase.ordinal == phase.ordinal + 1

        expected_sc_count = len(mock_adjudication_data_basic["supply_centers"])
        assert SupplyCenter.objects.filter(phase=new_phase).count() == expected_sc_count

        expected_unit_count = len(mock_adjudication_data_basic["units"])
        assert Unit.objects.filter(phase=new_phase).count() == expected_unit_count

        assert PhaseState.objects.filter(phase=new_phase).count() == member_count

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.COMPLETED

    @pytest.mark.django_db
    def test_resolve_can_retry_after_rollback(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        initial_phase_count = Phase.objects.count()

        with patch("phase.models.resolve") as mock_resolve:
            mock_resolve.return_value = mock_adjudication_data_basic

            original_method = Phase.objects.create_from_adjudication_data
            call_count = [0]

            def fail_first_time(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Simulated first attempt failure")
                return original_method(*args, **kwargs)

            with patch.object(Phase.objects, "create_from_adjudication_data", side_effect=fail_first_time):
                with pytest.raises(Exception, match="Simulated first attempt failure"):
                    Phase.objects.resolve(phase)

                assert Phase.objects.count() == initial_phase_count
                phase.refresh_from_db()
                assert phase.status == PhaseStatus.ACTIVE

                Phase.objects.resolve(phase)

        assert Phase.objects.count() == initial_phase_count + 1
        new_phase = phase.game.phases.last()
        assert new_phase is not None
        assert new_phase.status == PhaseStatus.ACTIVE

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.COMPLETED

    @pytest.mark.django_db
    def test_resolve_prevents_duplicate_active_phases(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
    ):
        phase = italy_vs_germany_phase_with_orders
        game = phase.game

        assert Phase.objects.filter(game=game, status=PhaseStatus.ACTIVE).count() == 1

        with patch("phase.models.resolve") as mock_resolve:
            mock_resolve.return_value = mock_adjudication_data_basic

            original_method = Phase.objects.create_from_adjudication_data

            def fail_before_marking_complete(*args, **kwargs):
                result = original_method(*args, **kwargs)
                raise Exception("Simulated failure before marking previous phase complete")

            with patch.object(Phase.objects, "create_from_adjudication_data", side_effect=fail_before_marking_complete):
                with pytest.raises(Exception, match="Simulated failure before marking previous phase complete"):
                    Phase.objects.resolve(phase)

        active_phases = Phase.objects.filter(game=game, status=PhaseStatus.ACTIVE)
        assert active_phases.count() == 1
        assert active_phases.first().id == phase.id


class TestFilterDuePhasesBasicFiltering:

    @pytest.mark.django_db
    def test_filter_due_phases_past_scheduled_resolution(self, phase_factory, classical_england_nation):
        phase = phase_factory(
            scheduled_resolution=timezone.now() - timedelta(hours=1),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False}
            ],
        )

        phases = Phase.objects.filter_due_phases()

        assert phase in phases

    @pytest.mark.django_db
    def test_filter_due_phases_future_scheduled_resolution_not_confirmed(
        self, phase_factory, classical_england_nation, classical_france_nation
    ):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
                {"nation": classical_france_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )

        phases = Phase.objects.filter_due_phases()

        assert phase not in phases

    @pytest.mark.django_db
    def test_filter_due_phases_future_scheduled_resolution_all_confirmed(
        self, phase_factory, classical_england_nation, classical_france_nation
    ):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(hours=24),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
                {"nation": classical_france_nation, "has_possible_orders": True, "orders_confirmed": True},
            ],
        )

        phases = Phase.objects.filter_due_phases()

        assert phase in phases


class TestPhaseAdminQueryPerformance:

    @pytest.mark.django_db
    def test_admin_changelist_query_count_simple(
        self, authenticated_client, active_game_with_phase_state, primary_user
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        url = "/admin/phase/phase/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200
        query_count = len(connection.queries)
        assert query_count == 10

    @pytest.mark.django_db
    def test_admin_changelist_query_count_with_multiple_phases(
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

        for i in range(3):
            game = Game.objects.create(
                name=f"Game {i}",
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

        url = "/admin/phase/phase/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200
        query_count = len(connection.queries)
        assert query_count == 10

    @pytest.mark.django_db
    def test_admin_changelist_query_count_with_many_phases(
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

        for i in range(5):
            game = Game.objects.create(
                name=f"Game {i}",
                variant=classical_variant,
                status=GameStatus.ACTIVE,
            )
            game.members.create(user=primary_user, nation=classical_england_nation)

            for j in range(4):
                phase = game.phases.create(
                    game=game,
                    variant=game.variant,
                    season="Spring" if j % 2 == 0 else "Fall",
                    year=1901 + (j // 2),
                    type="Movement",
                    status=PhaseStatus.ACTIVE if j == 3 else PhaseStatus.COMPLETED,
                    ordinal=j + 1,
                )
                phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
                phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

                # Create phase states to test prefetch
                for member in game.members.all():
                    phase.phase_states.create(member=member)

        url = "/admin/phase/phase/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200
        query_count = len(connection.queries)
        assert query_count == 10


class TestPhaseAdminNavigationLinks:

    @pytest.mark.django_db
    def test_view_units_link_with_units(
        self,
        authenticated_client,
        active_game_with_phase_state,
        primary_user,
        classical_england_nation,
        classical_london_province,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        phase = active_game_with_phase_state.current_phase
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        url = "/admin/phase/phase/"
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # Check that the link is in the response
        content = response.content.decode()
        assert f'href="/admin/unit/unit/?phase__id__exact={phase.id}"' in content
        assert f"{phase.units.count()} units" in content

    @pytest.mark.django_db
    def test_view_units_link_without_units(
        self,
        authenticated_client,
        active_game_with_phase_state,
        primary_user,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        url = "/admin/phase/phase/"
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # Should show "-" when no units
        content = response.content.decode()
        assert "-" in content

    @pytest.mark.django_db
    def test_view_supply_centers_link_with_supply_centers(
        self,
        authenticated_client,
        active_game_with_phase_state,
        primary_user,
        classical_england_nation,
        classical_london_province,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        phase = active_game_with_phase_state.current_phase
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)

        url = "/admin/phase/phase/"
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # Check that the link is in the response
        content = response.content.decode()
        assert f'href="/admin/supply_center/supplycenter/?phase__id__exact={phase.id}"' in content
        assert f"{phase.supply_centers.count()} supply centers" in content

    @pytest.mark.django_db
    def test_view_phase_states_link_with_phase_states(
        self,
        authenticated_client,
        active_game_with_phase_state,
        primary_user,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        phase = active_game_with_phase_state.current_phase

        url = "/admin/phase/phase/"
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # Check that the link is in the response
        assert f'href="/admin/phase/phasestate/?phase__id__exact={phase.id}"' in response.content.decode()
        phase_states_count = phase.phase_states.count()
        assert f"{phase_states_count} phase states" in response.content.decode()

    @pytest.mark.django_db
    def test_navigation_links_follow_to_filtered_pages(
        self,
        authenticated_client,
        active_game_with_phase_state,
        primary_user,
        classical_england_nation,
        classical_london_province,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        phase = active_game_with_phase_state.current_phase
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_london_province)

        # Follow the units link
        url = f"/admin/unit/unit/?phase__id__exact={phase.id}"
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # Verify the unit is shown in the filtered list
        assert classical_london_province.name in response.content.decode()


class TestPhaseAdminCustomActions:

    @pytest.mark.django_db
    def test_dry_run_resolution_action_success(
        self,
        authenticated_client,
        active_game_with_phase_state,
        primary_user,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        phase = active_game_with_phase_state.current_phase

        with patch("phase.admin.resolve") as mock_resolve:
            mock_resolve.return_value = {
                "season": "Spring",
                "year": 1901,
                "type": "Movement",
                "resolutions": [],
                "units": [],
                "supply_centers": [],
            }

            url = "/admin/phase/phase/"
            data = {
                "action": "dry_run_resolution",
                "_selected_action": [str(phase.id)],
            }
            response = authenticated_client.post(url, data, follow=True)

            assert response.status_code == 200
            mock_resolve.assert_called_once_with(phase)

    @pytest.mark.django_db
    def test_dry_run_resolution_requires_single_phase(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        classical_england_nation,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        # Create two phases
        game = Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)

        phase1 = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )

        phase2 = game.phases.create(
            game=game,
            variant=game.variant,
            season="Fall",
            year=1901,
            type="Movement",
            status=PhaseStatus.COMPLETED,
            ordinal=2,
        )

        url = "/admin/phase/phase/"
        data = {
            "action": "dry_run_resolution",
            "_selected_action": [str(phase1.id), str(phase2.id)],
        }
        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        assert "Please select exactly one phase" in response.content.decode()

    @pytest.mark.django_db
    def test_revert_to_phase_action_success(
        self,
        authenticated_client,
        game_with_three_phases,
        primary_user,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        phase1 = game_with_three_phases.phases.get(ordinal=1)

        url = "/admin/phase/phase/"
        data = {
            "action": "revert_to_phase",
            "_selected_action": [str(phase1.id)],
        }
        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        assert "Successfully reverted" in response.content.decode()

        # Verify phases 2 and 3 were deleted
        assert not game_with_three_phases.phases.filter(ordinal=2).exists()
        assert not game_with_three_phases.phases.filter(ordinal=3).exists()

    @pytest.mark.django_db
    def test_show_all_orders_action(
        self,
        authenticated_client,
        italy_vs_germany_phase_with_orders,
        primary_user,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        phase = italy_vs_germany_phase_with_orders

        url = "/admin/phase/phase/"
        data = {
            "action": "show_all_orders",
            "_selected_action": [str(phase.id)],
        }
        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        content = response.content.decode()

        # Should show orders as JSON
        assert "Orders for" in content
        assert "Total:" in content
