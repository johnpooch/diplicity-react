import pytest
from django.contrib.auth import get_user_model
from django.apps import apps
from game import models
from user_profile.models import UserProfile
from rest_framework.test import APIClient
from unittest.mock import MagicMock, patch
from variant.models import Variant
from common.constants import PhaseStatus, OrderType, UnitType

User = get_user_model()


@pytest.fixture
def pending_game_created_by_primary_user(db, primary_user, base_pending_game_for_primary_user, base_pending_phase):
    """
    Creates a pending game created by the primary user.
    """
    base_pending_phase(base_pending_game_for_primary_user)
    base_pending_game_for_primary_user.members.create(user=primary_user)
    return base_pending_game_for_primary_user


@pytest.fixture
def pending_game_created_by_secondary_user(
    db, secondary_user, base_pending_game_for_secondary_user, base_pending_phase
):
    """
    Creates a pending game created by the secondary user.
    """
    base_pending_phase(base_pending_game_for_secondary_user)
    base_pending_game_for_secondary_user.members.create(user=secondary_user)
    return base_pending_game_for_secondary_user


@pytest.fixture
def pending_game_created_by_secondary_user_joined_by_primary(db, primary_user, pending_game_created_by_secondary_user):
    """
    Creates a pending game created by the secondary user that the primary user has joined.
    """
    pending_game_created_by_secondary_user.members.create(user=primary_user)
    return pending_game_created_by_secondary_user


@pytest.fixture
def active_game_created_by_primary_user(db, primary_user, base_active_game_for_primary_user, base_active_phase):
    """
    Creates an active game created by the primary user.
    """
    base_active_phase(base_active_game_for_primary_user)
    base_active_game_for_primary_user.members.create(user=primary_user)
    return base_active_game_for_primary_user


@pytest.fixture
def active_game_created_by_secondary_user(db, secondary_user, base_active_game_for_secondary_user, base_active_phase):
    """
    Creates an active game created by the secondary user.
    """
    base_active_phase(base_active_game_for_secondary_user)
    base_active_game_for_secondary_user.members.create(user=secondary_user)
    return base_active_game_for_secondary_user


@pytest.fixture
def active_game_created_by_secondary_user_joined_by_primary(db, primary_user, active_game_created_by_secondary_user):
    """
    Creates an active game created by the secondary user that the primary user has joined.
    """
    active_game_created_by_secondary_user.members.create(user=primary_user)
    return active_game_created_by_secondary_user


@pytest.fixture
def mock_adjudication_service():
    """
    Create a mock adjudication service with default return values.
    """
    mock = MagicMock()
    mock.start.return_value = {
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
    mock.resolve.return_value = {
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
    return mock


@pytest.fixture
def mock_notify_task():
    """
    Create a mock for NotificationService.notify.
    """
    with patch("game.services.notification_service.NotificationService.notify") as mock:
        yield mock


@pytest.fixture
def mock_resolve_task():
    """
    Create a mock for GameService.resolve.
    """
    with patch("game.services.game_service.GameService.resolve") as mock:
        yield mock


@pytest.fixture
def game_service(primary_user, mock_adjudication_service):
    """
    Create a GameService instance with mocked adjudication service.
    """
    from game.services import GameService

    return GameService(user=primary_user, adjudication_service=mock_adjudication_service)


@pytest.fixture
def adjudication_service(primary_user):
    """
    Create an AdjudicationService instance.
    """
    from game.services import AdjudicationService

    return AdjudicationService(primary_user)


@pytest.fixture
def active_game_with_orders(
    db,
    active_game_with_phase_state,
    classical_london_province,
    classical_english_channel_province,
):
    """
    Creates an active game with orders for the primary user.
    """
    phase_state = active_game_with_phase_state.current_phase.phase_states.first()
    Order = apps.get_model("order", "Order")
    order = Order.objects.create(
        phase_state=phase_state,
        order_type="Move",
        source=classical_london_province,
        target=classical_english_channel_province,
    )
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_multiple_orders(
    db,
    active_game_with_phase_state,
    classical_english_channel_province,
    classical_liverpool_province,
    classical_london_province,
):
    """
    Creates an active game with multiple orders for the primary user.
    """
    phase_state = active_game_with_phase_state.current_phase.phase_states.first()
    Order = apps.get_model("order", "Order")
    Order.objects.create(
        phase_state=phase_state,
        order_type="Move",
        source=classical_london_province,
        target=classical_english_channel_province,
    )
    Order.objects.create(
        phase_state=phase_state,
        order_type=OrderType.SUPPORT,
        source=classical_liverpool_province,
        target=classical_london_province,
        aux=classical_english_channel_province,
    )
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_completed_phase_and_resolutions(db, active_game_with_multiple_orders):
    """
    Creates an active game with a completed phase and order resolutions.
    """
    game = active_game_with_multiple_orders
    phase = game.current_phase
    phase.status = PhaseStatus.COMPLETED
    phase.save()

    # Create resolutions for orders
    for order in phase.phase_states.first().orders.all():
        OrderResolution = apps.get_model("order", "OrderResolution")
        OrderResolution.objects.create(
            order=order,
            status="OK" if order.order_type == "Move" else "ErrInvalidSupporteeOrder",
            by=None,
        )

    return game


@pytest.fixture
def active_game_with_private_channel(db, active_game_with_phase_state):
    """
    Creates an active game with a private channel where the primary user is a member.
    """
    private_channel = active_game_with_phase_state.channels.create(name="Private Channel", private=True)
    private_channel.members.add(active_game_with_phase_state.members.first())
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_public_channel(db, active_game_with_phase_state):
    """
    Creates an active game with a public channel.
    """
    public_channel = active_game_with_phase_state.channels.create(name="Public Channel", private=False)
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_channels(db, active_game_with_phase_state, secondary_user):
    """
    Creates an active game with multiple channels and a secondary user.
    """
    private_member_channel = active_game_with_phase_state.channels.create(name="Private Member", private=True)
    private_member_channel.members.add(active_game_with_phase_state.members.first())
    private_member_channel.messages.create(sender=active_game_with_phase_state.members.first(), body="Test message")

    # Create private channel where primary user is not member
    private_non_member_channel = active_game_with_phase_state.channels.create(name="Private Non-Member", private=True)

    # Create public channel
    public_channel = active_game_with_phase_state.channels.create(name="Public Channel", private=False)

    # Add secondary user to game
    active_game_with_phase_state.members.create(user=secondary_user, nation="France")

    return active_game_with_phase_state


@pytest.fixture
def game_with_two_members(db, active_game_with_phase_state, secondary_user, england_nation, france_nation):
    """
    Creates a game with two members (primary and secondary user).
    """
    game = active_game_with_phase_state
    game.members.first().nation = england_nation
    game.members.first().save()

    game.members.create(user=secondary_user, nation=france_nation)

    return game


@pytest.fixture
def game_with_phase_and_units(
    db,
    game_with_two_members,
    classical_england_nation,
    classical_france_nation,
    classical_london_province,
    classical_liverpool_province,
    classical_irish_sea_province,
    classical_wales_province,
):
    """
    Creates a game with a phase and units for both members.
    """
    game = game_with_two_members
    phase = game.current_phase

    # Create units for England
    phase.units.create(type=UnitType.FLEET, nation=classical_england_nation, province=classical_london_province)
    phase.units.create(type=UnitType.ARMY, nation=classical_england_nation, province=classical_liverpool_province)

    # Create units for France
    phase.units.create(type=UnitType.FLEET, nation=classical_france_nation, province=classical_irish_sea_province)
    phase.units.create(type=UnitType.ARMY, nation=classical_france_nation, province=classical_wales_province)

    return game


@pytest.fixture
def game_with_phase_and_orders(
    db,
    game_with_phase_and_units,
    classical_england_nation,
    classical_france_nation,
    classical_london_province,
    classical_liverpool_province,
    classical_irish_sea_province,
    classical_wales_province,
    classical_english_channel_province,
):
    """
    Creates a game with a phase, units, and orders for both members.
    """
    game = game_with_phase_and_units
    phase = game.current_phase

    # Create orders for England
    england_phase_state = phase.phase_states.get(member__nation=classical_england_nation)
    england_phase_state.orders.create(
        order_type=OrderType.MOVE, source=classical_london_province, target=classical_english_channel_province
    )
    england_phase_state.orders.create(
        order_type=OrderType.SUPPORT,
        source=classical_liverpool_province,
        target=classical_london_province,
        aux=classical_english_channel_province,
    )

    # Create orders for France
    france_phase_state = phase.phase_states.get(member__nation=classical_france_nation)
    france_phase_state.orders.create(
        order_type=OrderType.MOVE, source=classical_irish_sea_province, target=classical_english_channel_province
    )
    france_phase_state.orders.create(
        order_type=OrderType.SUPPORT,
        source=classical_wales_province,
        target=classical_irish_sea_province,
        aux=classical_english_channel_province,
    )

    return game


@pytest.fixture
def game_with_retreat_phase(
    db, game_with_phase_and_units, classical_london_province, classical_wales_province, classical_england_nation
):
    """
    Creates a game with a retreat phase and a dislodged unit.
    """
    game = game_with_phase_and_units
    phase = game.current_phase
    phase.type = "Retreat"
    phase.save()

    # Create a dislodged unit
    phase.units.create(
        type=UnitType.FLEET,
        nation=classical_england_nation,
        province=classical_london_province,
        dislodged=True,
        dislodged_by=classical_wales_province,
    )

    return game
