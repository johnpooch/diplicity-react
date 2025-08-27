import pytest
from game import models

def get_unit(response, province, dislodged=False):
    """
    Helper function to get a unit from the response.
    """
    return next(
        unit
        for unit in response["phase"]["units"]
        if unit["province"] == province
        and unit.get("dislodged", False) == dislodged
    )

def get_resolution(response, province):
    """
    Helper function to get a resolution from the response.
    """
    return next(
        resolution
        for resolution in response["phase"]["resolutions"]
        if resolution["province"] == province
    )

def create_unit(phase, nation, province, unit_type, **kwargs):
    """
    Helper function to create a unit in a phase.
    """
    phase.units.create(type=unit_type, nation=nation, province=province, **kwargs)

def create_order(phase, nation, order_type, source, target=None, aux=None):
    """
    Helper function to create an order in a phase.
    """
    phase_state = phase.phase_states.get(member__nation=nation)
    phase_state.orders.create(
        order_type=order_type,
        source=source,
        target=target,
        aux=aux,
    )

@pytest.mark.django_db
def test_resolve_move(adjudication_service, game_with_two_members):
    """
    Test resolving a simple move order.
    """
    game = game_with_two_members
    phase = game.current_phase
    
    # Create unit and order
    create_unit(phase, "England", "lon", "Fleet")
    create_order(phase, "England", "Move", "lon", "eng")

    response = adjudication_service.resolve(game)

    # Check phase details
    assert response["phase"]["season"] == "Spring"
    assert response["phase"]["year"] == 1901
    assert response["phase"]["type"] == "Retreat"
    assert isinstance(response["phase"]["units"], list)

    # Check unit moved
    unit = get_unit(response, "eng")
    assert unit["type"] == "Fleet"
    assert unit["nation"] == "England"
    assert unit["province"] == "eng"

    # Check resolution
    resolution = get_resolution(response, "lon")
    assert resolution["province"] == "lon"
    assert resolution["result"] == "OK"

@pytest.mark.django_db
def test_resolve_move_to_source(adjudication_service, game_with_two_members):
    """
    Test resolving a move order to the source province.
    """
    game = game_with_two_members
    phase = game.current_phase
    
    # Create unit and order
    create_unit(phase, "England", "lon", "Fleet")
    create_order(phase, "England", "Move", "lon", "lon")

    response = adjudication_service.resolve(game)

    # Check unit didn't move
    unit = get_unit(response, "lon")
    assert unit["type"] == "Fleet"
    assert unit["nation"] == "England"
    assert unit["province"] == "lon"

    # Check resolution
    resolution = get_resolution(response, "lon")
    assert resolution["province"] == "lon"
    assert resolution["result"] == "ErrIllegalMove"
    assert resolution["by"] is None

@pytest.mark.django_db
def test_resolve_move_bounce(adjudication_service, game_with_two_members):
    """
    Test resolving a move order that results in a bounce.
    """
    game = game_with_two_members
    phase = game.current_phase
    
    # Create units and orders
    create_unit(phase, "England", "lon", "Fleet")
    create_unit(phase, "England", "lvp", "Army")
    create_order(phase, "England", "Move", "lon", "wal")
    create_order(phase, "England", "Move", "lvp", "wal")

    response = adjudication_service.resolve(game)

    # Check units didn't move
    unit = get_unit(response, "lon")
    assert unit["type"] == "Fleet"
    assert unit["nation"] == "England"
    assert unit["province"] == "lon"

    # Check resolution
    resolution = get_resolution(response, "lon")
    assert resolution["province"] == "lon"
    assert resolution["result"] == "ErrBounce"
    assert resolution["by"] == "lvp"

@pytest.mark.django_db
def test_resolve_successful_support_move(adjudication_service, game_with_two_members):
    """
    Test resolving a successful supported move.
    """
    game = game_with_two_members
    phase = game.current_phase
    
    # Create units and orders
    create_unit(phase, "England", "lon", "Fleet")
    create_unit(phase, "England", "lvp", "Army")
    create_order(phase, "England", "Move", "lon", "wal")
    create_order(phase, "England", "Support", "lvp", "lon", "wal")

    response = adjudication_service.resolve(game)

    # Check unit moved
    unit = get_unit(response, "wal")
    assert unit["type"] == "Fleet"
    assert unit["nation"] == "England"
    assert unit["province"] == "wal"

    # Check resolutions
    resolution_move = get_resolution(response, "lon")
    assert resolution_move["province"] == "lon"
    assert resolution_move["result"] == "OK"

    resolution_support = get_resolution(response, "lvp")
    assert resolution_support["province"] == "lvp"
    assert resolution_support["result"] == "OK"

@pytest.mark.django_db
def test_resolve_support_without_move(adjudication_service, game_with_two_members):
    """
    Test resolving a support order without a corresponding move.
    """
    game = game_with_two_members
    phase = game.current_phase
    
    # Create units and orders
    create_unit(phase, "England", "lon", "Fleet")
    create_unit(phase, "England", "lvp", "Army")
    create_order(phase, "England", "Hold", "lon")
    create_order(phase, "England", "Support", "lvp", "lon", "wal")

    response = adjudication_service.resolve(game)

    # Check unit didn't move
    unit = get_unit(response, "lon")
    assert unit["type"] == "Fleet"
    assert unit["nation"] == "England"
    assert unit["province"] == "lon"

    # Check resolution
    resolution_support = get_resolution(response, "lvp")
    assert resolution_support["province"] == "lvp"
    assert resolution_support["result"] == "ErrInvalidSupporteeOrder"
    assert resolution_support["by"] is None

@pytest.mark.django_db
def test_resolve_valid_retreat(adjudication_service, game_with_two_members):
    """
    Test resolving a valid retreat order.
    """
    game = game_with_two_members
    phase = game.current_phase
    phase.type = "Retreat"
    phase.save()
    
    # Create dislodged unit and retreat order
    create_unit(phase, "England", "lon", "Fleet", dislodged=True)
    create_order(phase, "England", "Move", "lon", "eng")

    response = adjudication_service.resolve(game)

    # Check unit retreated
    unit = get_unit(response, "eng")
    assert unit["type"] == "Fleet"
    assert unit["nation"] == "England"
    assert unit["province"] == "eng"

    # Check resolution
    resolution = get_resolution(response, "lon")
    assert resolution["province"] == "lon"
    assert resolution["result"] == "OK"

    # Check next phase
    assert response["phase"]["season"] == "Fall"
    assert response["phase"]["year"] == 1901
    assert response["phase"]["type"] == "Movement"

@pytest.mark.django_db
def test_resolve_invalid_retreat(adjudication_service, game_with_two_members):
    """
    Test resolving an invalid retreat order.
    """
    game = game_with_two_members
    phase = game.current_phase
    phase.type = "Retreat"
    phase.save()
    
    # Create dislodged unit and invalid retreat order
    create_unit(phase, "England", "lon", "Fleet", dislodged=True)
    create_order(phase, "England", "Move", "lon", "invalid_province")

    response = adjudication_service.resolve(game)

    # Check resolution
    resolution = get_resolution(response, "lon")
    assert resolution["province"] == "lon"
    assert resolution["result"] == "ErrInvalidDestination"

    # Check unit was removed
    try:
        dislodged_unit = get_unit(response, "lon", dislodged=True)
    except StopIteration:
        dislodged_unit = None
    assert dislodged_unit is None

    # Check next phase
    assert response["phase"]["season"] == "Fall"
    assert response["phase"]["year"] == 1901
    assert response["phase"]["type"] == "Movement" 