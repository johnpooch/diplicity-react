import pytest
from rest_framework import status
from django.apps import apps
from game import models
import json

@pytest.mark.django_db
def test_resolve_successful_move(game_service, active_game_with_orders, mock_notify_task):
    """
    Test that resolving a successful move creates the correct resolution.
    """
    game = game_service.resolve(active_game_with_orders.id)
    original_phase = game.phases.get(ordinal=1)
    
    # Verify resolution was created
    order = original_phase.phase_states.first().orders.first()
    resolution = apps.get_model('order', 'OrderResolution').objects.get(order=order)
    assert resolution.status == "OK"
    assert resolution.by is None

@pytest.mark.django_db
def test_resolve_bounce(game_service, active_game_with_orders, mock_notify_task):
    """
    Test that resolving a bounce creates the correct resolution.
    """
    # Update mock to return bounce result
    game_service.adjudication_service.resolve.return_value = {
        "phase": {
            "season": "Spring",
            "year": 1901,
            "type": "Retreat",
            "resolutions": [{"province": "lon", "result": "ErrBounce", "by": "lvp"}],
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

    game = game_service.resolve(active_game_with_orders.id)
    original_phase = game.phases.get(ordinal=1)
    
    # Verify resolution was created
    order = original_phase.phase_states.first().orders.first()
    resolution = apps.get_model('order', 'OrderResolution').objects.get(order=order)
    assert resolution.status == "ErrBounce"
    assert resolution.by == "lvp"

@pytest.mark.django_db
def test_resolve_invalid_support_order(game_service, active_game_with_orders, mock_notify_task):
    """
    Test that resolving an invalid support order creates the correct resolution.
    """
    # Update mock to return invalid support result
    game_service.adjudication_service.resolve.return_value = {
        "phase": {
            "season": "Spring",
            "year": 1901,
            "type": "Retreat",
            "resolutions": [{"province": "lon", "result": "ErrInvalidSupporteeOrder", "by": None}],
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

    game = game_service.resolve(active_game_with_orders.id)
    original_phase = game.phases.get(ordinal=1)
    
    # Verify resolution was created
    order = original_phase.phase_states.first().orders.first()
    resolution = apps.get_model('order', 'OrderResolution').objects.get(order=order)
    assert resolution.status == "ErrInvalidSupporteeOrder"
    assert resolution.by is None

@pytest.mark.django_db
def test_resolve_multiple_orders(game_service, active_game_with_multiple_orders, mock_notify_task):
    """
    Test that resolving multiple orders creates the correct resolutions.
    """
    # Update mock to return multiple resolutions
    game_service.adjudication_service.resolve.return_value = {
        "phase": {
            "season": "Spring",
            "year": 1901,
            "type": "Retreat",
            "resolutions": [
                {"province": "lon", "result": "OK", "by": None},
                {"province": "lvp", "result": "OK", "by": None},
            ],
            "units": [
                {
                    "type": "Fleet",
                    "nation": "England",
                    "province": "London",
                    "dislodged": False,
                    "dislodged_by": None,
                },
            ],
            "supply_centers": [{"province": "London", "nation": "England"}],
        },
        "options": {"England": {"option1": "value1"}},
    }

    game = game_service.resolve(active_game_with_multiple_orders.id)
    original_phase = game.phases.get(ordinal=1)

    orders = original_phase.phase_states.first().orders.all()
    assert len(orders) == 2
    
    for order in orders:
        resolution = apps.get_model('order', 'OrderResolution').objects.get(order=order)
        assert resolution.status == "OK"
        assert resolution.by is None

@pytest.mark.django_db
def test_resolve_adjudication_failure(game_service, active_game_with_orders):
    """
    Test that game resolution fails when adjudication service fails.
    """
    # Mock adjudication service to raise an exception
    game_service.adjudication_service.resolve.side_effect = Exception("Adjudication failed")

    with pytest.raises(Exception) as exc_info:
        game_service.resolve(active_game_with_orders.id)
    assert "Adjudication service failed" in str(exc_info.value)

    # Verify no resolutions were created
    assert apps.get_model('order', 'OrderResolution').objects.count() == 0
