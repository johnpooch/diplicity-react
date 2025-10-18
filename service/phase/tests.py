import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock
from rest_framework import status
from common.constants import PhaseStatus, PhaseType, OrderType, UnitType, GameStatus
from .models import Phase, PhaseState
from .serializers import PhaseStateSerializer
from .utils import transform_options
from order.models import Order


@pytest.mark.django_db
def test_confirm_phase_success(
    authenticated_client, active_game_with_phase_state, secondary_user, classical_france_nation
):
    """
    Test that an authenticated user can successfully confirm their phase.
    """
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
    """
    Test that confirming an already confirmed phase unconfirms it.
    """
    url = reverse("game-confirm-phase", args=[active_game_with_confirmed_phase_state.id])
    response = authenticated_client.put(url)
    assert response.status_code == status.HTTP_200_OK

    phase_state = active_game_with_confirmed_phase_state.current_phase.phase_states.first()
    assert not phase_state.orders_confirmed


@pytest.mark.django_db
def test_confirm_phase_game_not_active(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that confirming a phase in a non-active game returns 403.
    """
    url = reverse("game-confirm-phase", args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_not_member(authenticated_client, active_game_created_by_secondary_user):
    """
    Test that a non-member cannot confirm a phase.
    """
    url = reverse("game-confirm-phase", args=[active_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_eliminated(authenticated_client_for_secondary_user, active_game_with_eliminated_member):
    """
    Test that an eliminated user cannot confirm a phase.
    """
    url = reverse("game-confirm-phase", args=[active_game_with_eliminated_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_kicked(authenticated_client_for_secondary_user, active_game_with_kicked_member):
    """
    Test that a kicked user cannot confirm a phase.
    """
    url = reverse("game-confirm-phase", args=[active_game_with_kicked_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_unauthenticated(unauthenticated_client, active_game_with_phase_state):
    """
    Test that unauthenticated users cannot confirm a phase.
    """
    url = reverse("game-confirm-phase", args=[active_game_with_phase_state.id])
    response = unauthenticated_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_retrieve_orderable_provinces_success(authenticated_client, active_game_with_phase_options):
    """
    Test that an authenticated member can retrieve orderable provinces.
    """
    url = reverse("phase-state-retrieve", args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert "orderable_provinces" in response.data


@pytest.mark.django_db
def test_retrieve_orderable_provinces_not_member(authenticated_client, active_game_created_by_secondary_user):
    """
    Test that a non-member cannot retrieve orderable provinces.
    """
    url = reverse("phase-state-retrieve", args=[active_game_created_by_secondary_user.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_resolve_phases_success(authenticated_client):
    """
    Test that the phase resolve endpoint works.
    """
    url = reverse("phase-resolve-all")
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert "resolved" in response.data
    assert "failed" in response.data


@pytest.mark.django_db
def test_phase_should_resolve_immediately_no_users_with_orders(active_game_with_phase_state):
    """
    Test that a phase should resolve immediately when no users have possible orders.
    """
    phase = active_game_with_phase_state.current_phase
    phase.options = {"England": {}}
    phase.save()
    assert phase.should_resolve_immediately


@pytest.mark.django_db
def test_phase_should_resolve_immediately_all_confirmed(
    active_game_with_phase_state, godip_options_england_london_hold
):
    """
    Test that a phase should resolve immediately when all users with orders have confirmed.
    """
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
    """
    Test that a phase should NOT resolve immediately when some users with orders haven't confirmed.
    """
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
    """
    Test the nations_with_possible_orders property with various option configurations.
    """
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
    """
    Test that resolve_due_phases resolves phases when scheduled time has passed.
    """
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
    """
    Test that resolve_due_phases resolves phases that should resolve immediately.
    """
    phase = active_game_with_phase_state.current_phase

    future_time = timezone.now() + timedelta(hours=24)
    phase.scheduled_resolution = future_time
    phase.options = {}
    phase.save()
    with patch.object(Phase.objects, "resolve") as mock_resolve:
        result = Phase.objects.resolve_due_phases()
        assert result["resolved"] == 1
        assert result["failed"] == 0
        mock_resolve.assert_called_once_with(phase)


@pytest.mark.django_db
def test_resolve_due_phases_no_resolution_needed(active_game_with_phase_state, godip_options_england_london_hold):
    """
    Test that resolve_due_phases doesn't resolve phases that aren't ready.
    """
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


class TestAdjustmentPhaseOrderLimits:
    """
    Test adjustment phase order limits based on supply center vs unit counts.
    """

    @pytest.mark.django_db
    def test_max_allowed_orders_non_adjustment_phase(self, active_game_with_phase_state):
        """Test that non-adjustment phases have unlimited orders."""
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
        """Test that nations with surplus supply centers can build."""
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
        """Test that nations with surplus units must disband."""
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
        """Test that nations with balanced supply centers and units have no orders."""
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
        """Test that nations with no supply centers and no units are balanced."""
        phase = active_game_with_phase_state.current_phase
        phase.type = PhaseType.ADJUSTMENT
        phase.save()

        # Nation has 0 supply centers and 0 units (balanced)
        phase_state = phase.phase_states.first()
        assert phase_state.max_allowed_adjustment_orders() == 0

    @pytest.mark.django_db
    def test_orderable_provinces_movement_phase_no_limit(self, active_game_with_phase_state):
        """Test that movement phases don't apply order limits."""
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
        """Test that adjustment phases show all provinces when under order limit."""
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
        """Test that adjustment phases show only existing order provinces when at limit with no orders."""
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
        """Test that adjustment phases show only existing order provinces when at limit."""
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
        """Test that balanced nations cannot create any orders."""
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
        """Test that users can edit existing orders when at the limit."""
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
        """Test that nations with large surpluses can build multiple units."""
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
        """
        Test transforming a simple Hold order removes SrcProvince layer.
        """
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
        """
        Test transforming a Move order removes SrcProvince layer and exposes targets.
        """
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
        """
        Test transforming a Support order removes SrcProvince layer and preserves aux/target structure.
        """
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
        """
        Test transforming a Convoy order removes SrcProvince layer and preserves aux/target structure.
        """
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
        """
        Test transforming an army moving to a province with named coasts.
        Army uses parent province, not specific coasts.
        """
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
        """
        Test transforming an army moving FROM a province with named coasts.
        The orderable province is the parent, army can move regardless of coast.
        """
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
        """
        Test transforming a fleet moving FROM a named coast province.
        Orderable province is parent but SrcProvince confirms specific coast.
        """
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
        """
        Test transforming a fleet moving TO a named coast province.
        Should group spa/nc and spa/sc under spa with coast selection.
        """
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
        """
        Test transforming a fleet moving to ONLY ONE named coast.
        Should still group under parent for consistency.
        """
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
        """
        Test transforming a simple Build Army order in a landlocked province.
        """
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
        """
        Test transforming a Build order in a coastal province.
        Both Army and Fleet options should be available.
        """
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
        """
        Test transforming Build orders in a province with named coasts.
        Should merge stp/nc and stp/sc into single stp entry.
        Army uses parent, Fleet adds coast selection step.
        """
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
        assert dislodged_unit.dislodged_by is not None

        dislodging_unit = phase.units.get(province__province_id="ven")
        assert dislodged_unit.dislodged_by == dislodging_unit

        attacker_unit = new_phase.units.get(province__province_id="kie", nation__name="Italy")
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
            province=italy_vs_germany_venice_province,
            type=UnitType.ARMY,
            nation=italy_vs_germany_italy_nation
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

        order_resolutions_phase2 = [
            order.resolution for order in phase2.all_orders if hasattr(order, 'resolution')
        ]
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
