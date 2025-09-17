import pytest
from django.core.management import call_command
from django.utils import timezone
from game.models import Game, Phase
from unittest.mock import patch
from io import StringIO

@pytest.mark.django_db
def test_no_due_phases(capfd):
    # No phases are due
    call_command('resolve_due_phases')
    out = capfd.readouterr().out
    assert "No due phases to resolve." in out

@pytest.mark.django_db
def test_due_phase_calls_resolve(db, primary_user, classical_variant):
    # Create a game and a due phase
    game = Game.objects.create(name="Test Game", status=Game.ACTIVE, variant=classical_variant)
    phase = Phase.objects.create(
        game=game,
        status=Phase.ACTIVE,
        season="Spring",
        year=1901,
        type="Movement",
        scheduled_resolution=timezone.now() - timezone.timedelta(seconds=1),
    )
    with patch("game.services.game_service.GameService.resolve") as mock_resolve:
        call_command('resolve_due_phases')
        mock_resolve.assert_called_once_with(game.id)

@pytest.mark.django_db
def test_due_phase_error_handling(db, primary_user, classical_variant):
    # Create a game and a due phase
    game = Game.objects.create(name="Test Game", status=Game.ACTIVE, variant=classical_variant)
    phase = Phase.objects.create(
        game=game,
        status=Phase.ACTIVE,
        season="Spring",
        year=1901,
        type="Movement",
        scheduled_resolution=timezone.now() - timezone.timedelta(seconds=1),
    )
    with patch("game.services.game_service.GameService.resolve", side_effect=Exception("fail!")):
        out = StringIO()
        call_command('resolve_due_phases', stdout=out)
        output = out.getvalue()
        assert "Failed to resolve phase for game" in output
        assert "fail!" in output 