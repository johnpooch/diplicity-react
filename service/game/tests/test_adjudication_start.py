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

def get_supply_center(response, province):
    """
    Helper function to get a supply center from the response.
    """
    return next(
        supply_center
        for supply_center in response["phase"]["supply_centers"]
        if supply_center["province"] == province
    )

@pytest.mark.django_db
def test_start_classical(adjudication_service, active_game_with_phase_state):
    """
    Test starting a classical game.
    """
    game = active_game_with_phase_state
    response = adjudication_service.start(game)

    # Check phase details
    assert response["phase"]["season"] == "Spring"
    assert response["phase"]["year"] == 1901
    assert response["phase"]["type"] == "Movement"
    assert isinstance(response["phase"]["units"], list)
    assert isinstance(response["phase"]["supply_centers"], list)
    assert response["phase"]["resolutions"] == []

    # Check a specific unit (Turkey's fleet in Ankara)
    unit = get_unit(response, "ank")
    assert unit["type"] == "Fleet"
    assert unit["nation"] == "Turkey"
    assert unit["province"] == "ank"

    # Check a specific supply center (Turkey's Ankara)
    supply_center = get_supply_center(response, "ank")
    assert supply_center["province"] == "ank"
    assert supply_center["nation"] == "Turkey"

    # Check options
    assert isinstance(response["options"], dict) 