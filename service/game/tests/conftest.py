import pytest
from django.contrib.auth import get_user_model
from game import models
from rest_framework.test import APIClient
from unittest.mock import MagicMock, patch

User = get_user_model()

@pytest.fixture(scope="session")
def primary_user(django_db_setup, django_db_blocker):
    """
    Create the primary test user.
    """
    with django_db_blocker.unblock():
        return User.objects.create_user(
            username="primaryuser",
            email="primary@example.com",
            password="testpass123"
        )

@pytest.fixture(scope="session")
def secondary_user(django_db_setup, django_db_blocker):
    """
    Create another test user.
    """
    with django_db_blocker.unblock():
        return User.objects.create_user(
            username="secondaryuser",
            email="secondary@example.com",
            password="testpass123"
        )

@pytest.fixture(scope="session")
def tertiary_user(django_db_setup, django_db_blocker):
    """
    Create a test user.
    """
    with django_db_blocker.unblock():
        return User.objects.create_user(
            username="tertiaryuser",
            email="tertiary@example.com",
            password="testpass123"
        )

@pytest.fixture(scope="session")
def tertiary_user_profile(django_db_setup, django_db_blocker, tertiary_user):
    """
    Create a test user profile.
    """
    with django_db_blocker.unblock():
        return models.UserProfile.objects.create(
            user=tertiary_user,
            name="Tertiary User",
            picture=""
        )

@pytest.fixture(scope="session")
def primary_user_profile(django_db_setup, django_db_blocker, primary_user):
    """
    Create a test user profile.
    """
    with django_db_blocker.unblock():
        return models.UserProfile.objects.create(
            user=primary_user,
            name="Primary User",
            picture=""
        )

@pytest.fixture(scope="session")
def secondary_user_profile(django_db_setup, django_db_blocker, secondary_user):
    """
    Create a test user profile.
    """
    with django_db_blocker.unblock():
        return models.UserProfile.objects.create(
            user=secondary_user,
            name="Secondary User",
            picture=""
        )

@pytest.fixture(scope="session")
def authenticated_client(primary_user):
    """
    Create an authenticated client.
    """
    client = APIClient()
    client.force_authenticate(user=primary_user)
    return client

@pytest.fixture(scope="session")
def authenticated_client_for_secondary_user(secondary_user):
    """
    Create an authenticated client for the secondary user.
    """
    client = APIClient()
    client.force_authenticate(user=secondary_user)
    return client

@pytest.fixture(scope="session")
def authenticated_client_for_tertiary_user(tertiary_user):
    """
    Create an authenticated client for the tertiary user.
    """
    client = APIClient()
    client.force_authenticate(user=tertiary_user)
    return client

@pytest.fixture(scope="session")
def unauthenticated_client():
    """
    Create an unauthenticated client.
    """
    return APIClient()

@pytest.fixture(scope="session")
def italy_vs_germany_variant(django_db_setup, django_db_blocker):
    """
    Create a test variant.
    """
    with django_db_blocker.unblock():
        return models.Variant.objects.get(id="italy-vs-germany")

@pytest.fixture(scope="session")
def classical_variant(django_db_setup, django_db_blocker):
    """
    Create a test variant.
    """
    with django_db_blocker.unblock():
        return models.Variant.objects.get(id="classical")

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
def mock_start_task():
    """
    Create a mock for start_task.delay.
    """
    with patch("game.tasks.start_task.delay") as mock:
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
def adjudication_service(primary_user):
    """
    Create an AdjudicationService instance.
    """
    from game.services import AdjudicationService
    return AdjudicationService(primary_user)

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

@pytest.fixture
def active_game_with_completed_phase_and_resolutions(db, active_game_with_multiple_orders):
    """
    Creates an active game with a completed phase and order resolutions.
    """
    game = active_game_with_multiple_orders
    phase = game.current_phase
    phase.status = models.Phase.COMPLETED
    phase.save()

    # Create resolutions for orders
    for order in phase.phase_states.first().orders.all():
        models.OrderResolution.objects.create(
            order=order,
            status="OK" if order.order_type == "Move" else "ErrInvalidSupporteeOrder",
            by=None
        )

    return game

@pytest.fixture
def active_game_with_phase_options(db, active_game_with_phase_state):
    """
    Creates an active game with phase options loaded from options.json.
    """
    import json
    from django.conf import settings

    phase = active_game_with_phase_state.current_phase
    with open(f"{settings.BASE_DIR}/game/data/options/options.json") as f:
        json_string = f.read()
    phase.options = json.dumps(json.loads(json_string))
    phase.save()
    return active_game_with_phase_state

@pytest.fixture
def active_game_with_private_channel(db, active_game_with_phase_state):
    """
    Creates an active game with a private channel where the primary user is a member.
    """
    private_channel = active_game_with_phase_state.channels.create(
        name="Private Channel",
        private=True
    )
    private_channel.members.add(active_game_with_phase_state.members.first())
    return active_game_with_phase_state

@pytest.fixture
def active_game_with_public_channel(db, active_game_with_phase_state):
    """
    Creates an active game with a public channel.
    """
    public_channel = active_game_with_phase_state.channels.create(
        name="Public Channel",
        private=False
    )
    return active_game_with_phase_state

@pytest.fixture
def active_game_with_channels(db, active_game_with_phase_state, secondary_user):
    """
    Creates an active game with multiple channels and a secondary user.
    """
    private_member_channel = active_game_with_phase_state.channels.create(
        name="Private Member",
        private=True
    )
    private_member_channel.members.add(active_game_with_phase_state.members.first())
    private_member_channel.messages.create(sender=active_game_with_phase_state.members.first(), body="Test message")

    # Create private channel where primary user is not member
    private_non_member_channel = active_game_with_phase_state.channels.create(
        name="Private Non-Member",
        private=True
    )

    # Create public channel
    public_channel = active_game_with_phase_state.channels.create(
        name="Public Channel",
        private=False
    )

    # Add secondary user to game
    active_game_with_phase_state.members.create(
        user=secondary_user,
        nation="France"
    )

    return active_game_with_phase_state

@pytest.fixture
def mock_google_auth():
    """
    Create a mock for Google ID token verification.
    """
    with patch("game.services.auth_service.google_id_token.verify_oauth2_token") as mock:
        mock.return_value = {
            "iss": "accounts.google.com",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/picture.jpg",
        }
        yield mock

@pytest.fixture
def mock_refresh_token():
    """
    Create a mock for refresh token generation.
    """
    with patch("game.services.auth_service.RefreshToken.for_user") as mock:
        mock.return_value = type(
            "MockRefreshToken",
            (object,),
            {
                "access_token": "access_token",
                "__str__": lambda self: "refresh_token",
            },
        )()
        yield mock

@pytest.fixture
def game_with_two_members(db, active_game_with_phase_state, secondary_user):
    """
    Creates a game with two members (primary and secondary user).
    """
    game = active_game_with_phase_state
    game.members.first().nation = "England"
    game.members.first().save()
    
    game.members.create(
        user=secondary_user,
        nation="France"
    )

    return game

@pytest.fixture
def game_with_phase_and_units(db, game_with_two_members):
    """
    Creates a game with a phase and units for both members.
    """
    game = game_with_two_members
    phase = game.current_phase
    
    # Create units for England
    phase.units.create(type="Fleet", nation="England", province="lon")
    phase.units.create(type="Army", nation="England", province="lvp")
    
    # Create units for France
    phase.units.create(type="Fleet", nation="France", province="iri")
    phase.units.create(type="Army", nation="France", province="wal")
    
    return game

@pytest.fixture
def game_with_phase_and_orders(db, game_with_phase_and_units):
    """
    Creates a game with a phase, units, and orders for both members.
    """
    game = game_with_phase_and_units
    phase = game.current_phase
    
    # Create orders for England
    england_phase_state = phase.phase_states.get(member__nation="England")
    england_phase_state.orders.create(
        order_type="Move",
        source="lon",
        target="eng"
    )
    england_phase_state.orders.create(
        order_type="Support",
        source="lvp",
        target="lon",
        aux="eng"
    )
    
    # Create orders for France
    france_phase_state = phase.phase_states.get(member__nation="France")
    france_phase_state.orders.create(
        order_type="Move",
        source="iri",
        target="eng"
    )
    france_phase_state.orders.create(
        order_type="Support",
        source="wal",
        target="iri",
        aux="eng"
    )
    
    return game

@pytest.fixture
def game_with_retreat_phase(db, game_with_phase_and_units):
    """
    Creates a game with a retreat phase and a dislodged unit.
    """
    game = game_with_phase_and_units
    phase = game.current_phase
    phase.type = "Retreat"
    phase.save()
    
    # Create a dislodged unit
    phase.units.create(
        type="Fleet",
        nation="England",
        province="lon",
        dislodged=True,
        dislodged_by="wal"
    )
    
    return game
