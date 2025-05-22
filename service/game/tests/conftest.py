import pytest
from django.contrib.auth import get_user_model
from game import models
from rest_framework.test import APIClient
from unittest.mock import MagicMock, patch

User = get_user_model()

@pytest.fixture
def primary_user(db):
    """
    Create the primary test user.
    """
    return User.objects.create_user(
        username="primaryuser",
        email="primary@example.com",
        password="testpass123"
    )

@pytest.fixture
def secondary_user(db):
    """
    Create another test user.
    """
    return User.objects.create_user(
        username="secondaryuser",
        email="secondary@example.com",
        password="testpass123"
    )

@pytest.fixture
def primary_user_profile(db, primary_user):
    """
    Create a test user profile.
    """
    return models.UserProfile.objects.create(
        user=primary_user,
        name="Primary User",
        picture=""
    )

@pytest.fixture
def secondary_user_profile(db, secondary_user):
    """
    Create a test user profile.
    """
    return models.UserProfile.objects.create(
        user=secondary_user,
        name="Secondary User",
        picture=""
    )

@pytest.fixture
def authenticated_client(primary_user):
    """
    Create an authenticated client.
    """
    client = APIClient()
    client.force_authenticate(user=primary_user)
    return client

@pytest.fixture
def authenticated_client_for_secondary_user(secondary_user):
    """
    Create an authenticated client for the secondary user.
    """
    client = APIClient()
    client.force_authenticate(user=secondary_user)
    return client

@pytest.fixture
def unauthenticated_client():
    """
    Create an unauthenticated client.
    """
    return APIClient()

@pytest.fixture
def classical_variant(db):
    """
    Create a test variant.
    """
    return models.Variant.objects.create(
        id="classical",
        name="Classical"
    )

@pytest.fixture
def base_pending_game_for_primary_user(db, classical_variant):
    """
    Create a base pending game for the primary user.
    """
    return models.Game.objects.create(
        name="Primary User's Pending Game",
        variant=classical_variant,
        status=models.Game.PENDING
    )

@pytest.fixture
def base_pending_game_for_secondary_user(db, classical_variant):
    """
    Create a base pending game for the secondary user.
    """
    return models.Game.objects.create(
        name="Secondary User's Pending Game",
        variant=classical_variant,
        status=models.Game.PENDING
    )

@pytest.fixture
def base_active_game_for_primary_user(db, classical_variant):
    """
    Create a base active game for the primary user.
    """
    return models.Game.objects.create(
        name="Primary User's Active Game",
        variant=classical_variant,
        status=models.Game.ACTIVE
    )

@pytest.fixture
def base_active_game_for_secondary_user(db, classical_variant):
    """
    Create a base active game for the secondary user.
    """
    return models.Game.objects.create(
        name="Secondary User's Active Game",
        variant=classical_variant,
        status=models.Game.ACTIVE
    )

@pytest.fixture
def base_pending_phase(db):
    """
    Create a basic phase with units and supply centers.
    """
    def _create_phase(game):
        phase = game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
            status=models.Phase.PENDING
        )

        phase.units.create(
            type="Fleet",
            nation="England",
            province="edi"
        )

        phase.supply_centers.create(
            nation="England",
            province="edi"
        )

        return phase
    return _create_phase

@pytest.fixture
def base_active_phase(db):
    """
    Create a basic phase with units and supply centers.
    """
    def _create_phase(game):
        phase = game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
            status=models.Phase.ACTIVE
        )

        phase.units.create(
            type="Fleet",
            nation="England",
            province="edi"
        )

        phase.supply_centers.create(
            nation="England",
            province="edi"
        )

        return phase
    return _create_phase

@pytest.fixture
def pending_game_created_by_primary_user(db, primary_user, base_pending_game_for_primary_user, base_pending_phase):
    """
    Creates a pending game created by the primary user.
    """
    base_pending_phase(base_pending_game_for_primary_user)
    base_pending_game_for_primary_user.members.create(user=primary_user)
    return base_pending_game_for_primary_user

@pytest.fixture
def pending_game_created_by_secondary_user(db, secondary_user, base_pending_game_for_secondary_user, base_pending_phase):
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
    Create a mock for notify_task.apply_async.
    """
    with patch("game.tasks.notify_task.apply_async") as mock:
        yield mock

@pytest.fixture
def mock_resolve_task():
    """
    Create a mock for resolve_task.apply_async.
    """
    with patch("game.tasks.resolve_task.apply_async") as mock:
        mock_task_result = MagicMock(task_id=12345)
        mock.return_value = mock_task_result
        models.Task.objects.create(id=mock_task_result.task_id)
        yield mock

@pytest.fixture
def game_service(primary_user, mock_adjudication_service):
    """
    Create a GameService instance with mocked adjudication service.
    """
    from game.services import GameService
    return GameService(user=primary_user, adjudication_service=mock_adjudication_service)

@pytest.fixture
def active_game_with_phase_state(db, primary_user, base_active_game_for_primary_user, base_active_phase):
    """
    Creates an active game with a phase state for the primary user.
    """
    phase = base_active_phase(base_active_game_for_primary_user)
    member = base_active_game_for_primary_user.members.create(user=primary_user, nation="England")
    phase_state = phase.phase_states.create(member=member)
    return base_active_game_for_primary_user

@pytest.fixture
def active_game_with_confirmed_phase_state(db, active_game_with_phase_state):
    """
    Creates an active game with a confirmed phase state.
    """
    phase_state = active_game_with_phase_state.current_phase.phase_states.first()
    phase_state.orders_confirmed = True
    phase_state.save()
    return active_game_with_phase_state

@pytest.fixture
def active_game_with_eliminated_member(db, active_game_with_phase_state, secondary_user):
    """
    Creates an active game with an eliminated member.
    """
    member = active_game_with_phase_state.members.create(user=secondary_user, eliminated=True)
    active_game_with_phase_state.current_phase.phase_states.create(member=member)
    return active_game_with_phase_state

@pytest.fixture
def active_game_with_kicked_member(db, active_game_with_phase_state, secondary_user):
    """
    Creates an active game with a kicked member.
    """
    member = active_game_with_phase_state.members.create(user=secondary_user, kicked=True)
    active_game_with_phase_state.current_phase.phase_states.create(member=member)
    return active_game_with_phase_state

@pytest.fixture
def active_game_with_resolution_task(db, active_game_with_phase_state):
    """
    Creates an active game with a resolution task.
    """
    task = models.Task.objects.create()
    active_game_with_phase_state.resolution_task = task
    active_game_with_phase_state.save()
    return active_game_with_phase_state

@pytest.fixture
def active_game_with_orders(db, active_game_with_phase_state):
    """
    Creates an active game with orders for the primary user.
    """
    phase_state = active_game_with_phase_state.current_phase.phase_states.first()
    order = models.Order.objects.create(
        phase_state=phase_state,
        order_type="Move",
        source="lon",
        target="eng"
    )
    return active_game_with_phase_state

@pytest.fixture
def active_game_with_multiple_orders(db, active_game_with_phase_state):
    """
    Creates an active game with multiple orders for the primary user.
    """
    phase_state = active_game_with_phase_state.current_phase.phase_states.first()
    models.Order.objects.create(
        phase_state=phase_state,
        order_type="Move",
        source="lon",
        target="eng"
    )
    models.Order.objects.create(
        phase_state=phase_state,
        order_type="Support",
        source="lvp",
        target="lon",
        aux="eng"
    )
    return active_game_with_phase_state
