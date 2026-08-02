from datetime import timedelta

import pytest
from django.utils import timezone

from game.models import Game
from game.tasks import SANDBOX_RETENTION_DAYS, purge_stale_sandbox_games


class TestPurgeStaleSandboxGames:
    @pytest.mark.django_db
    def test_deletes_stale_sandbox_game(self, sandbox_game_factory, in_memory_procrastinate):
        stale = sandbox_game_factory()
        Game.objects.filter(id=stale.id).update(
            updated_at=timezone.now() - timedelta(days=SANDBOX_RETENTION_DAYS + 1)
        )

        purge_stale_sandbox_games(timestamp=0)

        assert not Game.objects.filter(id=stale.id).exists()

    @pytest.mark.django_db
    def test_keeps_recently_active_sandbox_game(self, sandbox_game_factory, in_memory_procrastinate):
        fresh = sandbox_game_factory()

        purge_stale_sandbox_games(timestamp=0)

        assert Game.objects.filter(id=fresh.id).exists()

    @pytest.mark.django_db
    def test_keeps_stale_non_sandbox_game(self, active_game_factory, in_memory_procrastinate):
        game = active_game_factory()
        Game.objects.filter(id=game.id).update(
            updated_at=timezone.now() - timedelta(days=SANDBOX_RETENTION_DAYS + 1)
        )

        purge_stale_sandbox_games(timestamp=0)

        assert Game.objects.filter(id=game.id).exists()
