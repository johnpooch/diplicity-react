from unittest.mock import patch

import pytest

from common.commands import Command
from common.policies import Denied
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db


class RenameGame(Command):
    decision = "can_manage"
    events = ["game_renamed"]

    def perform(self, game):
        self.locked = game
        game.name = self.data["name"]
        game.save(update_fields=["name"])
        return game

    def event_kwargs(self, event, game):
        return {"name": game.name}


class SkippedRename(RenameGame):
    def applies(self, game):
        return False


class CreateNothing(Command):
    events = ["nothing_created"]

    def perform(self, target):
        return "created"


class TestCommand:
    def test_performs_on_freshly_locked_row(self):
        game = GameFactory()
        command = RenameGame(actor=game.created_by, name="Renamed")
        with patch("common.commands.emit"):
            command(game)
        assert command.locked is not game
        assert command.locked.pk == game.pk

    def test_emits_declared_events_after_performing(self):
        game = GameFactory()
        with patch("common.commands.emit") as emit:
            RenameGame(actor=game.created_by, name="Renamed")(game)
        emit.assert_called_once_with("game_renamed", name="Renamed")

    def test_denied_decision_raises_without_performing(self):
        game = GameFactory()
        command = RenameGame(actor=UserFactory(), name="Renamed")
        with patch("common.commands.emit") as emit, pytest.raises(Denied):
            command(game)
        assert not hasattr(command, "locked")
        emit.assert_not_called()

    def test_inapplicable_target_is_skipped(self):
        game = GameFactory()
        with patch("common.commands.emit") as emit:
            assert SkippedRename(actor=game.created_by, name="Renamed")(game) is None
        emit.assert_not_called()

    def test_missing_target_row_is_skipped(self):
        game = GameFactory()
        game.pk = "missing-game"
        with patch("common.commands.emit"):
            assert RenameGame(actor=game.created_by, name="Renamed")(game) is None

    def test_command_without_target_performs_directly(self):
        with patch("common.commands.emit") as emit:
            assert CreateNothing()() == "created"
        emit.assert_called_once_with("nothing_created", actor=None)
