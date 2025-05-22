import pytest
from rest_framework import status
from game import models
import json

@pytest.mark.django_db
def test_start_game_updates_status(game_service, pending_game_created_by_primary_user, mock_notify_task, mock_resolve_task):
    """
    Test that starting a game updates the game and phase status correctly.
    """
    game = game_service.start(pending_game_created_by_primary_user.id)
    assert game.status == models.Game.ACTIVE
    assert game.current_phase.status == models.Phase.ACTIVE

@pytest.mark.django_db
def test_start_game_assigns_nations(game_service, pending_game_created_by_primary_user, mock_notify_task, mock_resolve_task):
    """
    Test that starting a game assigns nations to all members.
    """
    game = game_service.start(pending_game_created_by_primary_user.id)
    nations = [member.nation for member in game.members.all()]
    assert all(nations)  # Ensure all members have nations

@pytest.mark.django_db
def test_start_game_assigns_options(game_service, pending_game_created_by_primary_user, mock_notify_task, mock_resolve_task):
    """
    Test that starting a game assigns options to all nations.
    """
    game = game_service.start(pending_game_created_by_primary_user.id)
    for member in game.members.all():
        phase_state = models.PhaseState.objects.filter(
            phase=game.current_phase, member=member
        ).first()
        assert phase_state is not None
        expected_options = game_service.adjudication_service.start.return_value["options"].get(member.nation)
        assert json.loads(phase_state.options) == expected_options

@pytest.mark.django_db
def test_start_game_sends_notifications(game_service, pending_game_created_by_primary_user, mock_notify_task, mock_resolve_task):
    """
    Test that starting a game sends notifications to all members.
    """
    game = game_service.start(pending_game_created_by_primary_user.id)
    user_ids = [member.user.id for member in game.members.all()]
    mock_notify_task.assert_called_once_with(
        args=[
            user_ids,
            {
                "title": "Game Started",
                "body": f"Game '{game.name}' has started!",
                "game_id": game.id,
                "type": "game_start",
            },
        ],
        kwargs={},
    )

@pytest.mark.django_db
def test_start_game_adjudication_failure(game_service, pending_game_created_by_primary_user):
    """
    Test that game start fails when adjudication service fails.
    """
    game_service.adjudication_service.start.side_effect = Exception("Adjudication failed")

    with pytest.raises(Exception) as exc_info:
        game_service.start(pending_game_created_by_primary_user.id)
    assert "Adjudication service failed" in str(exc_info.value)

    game = models.Game.objects.get(id=pending_game_created_by_primary_user.id)
    assert game.status == models.Game.PENDING

@pytest.mark.django_db
def test_start_game_invalid_status(game_service, active_game_created_by_primary_user):
    """
    Test that a non-pending game cannot be started.
    """
    with pytest.raises(Exception) as exc_info:
        game_service.start(active_game_created_by_primary_user.id)
    assert "Cannot start a non-pending game" in str(exc_info.value)
