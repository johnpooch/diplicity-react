from django.utils import timezone

from common.commands import Command
from common.constants import CommitmentEvent, GameStatus, MemberKind
from variant.models import Variant

from .builders import GameBuilder
from .legacy import delete_game, legacy_game, legacy_phase, record_commitment
from .models import Game

SANDBOX_LIMIT = 3


class GameCommand(Command):
    def event_kwargs(self, event, game):
        return {"game": legacy_game(game), "actor": self.actor}


class StartingGameCommand(GameCommand):
    def start_when_full(self, game):
        if not game.is_full:
            return []
        if game.muster_required and game.muster_window_seconds is not None:
            game.enter_mustering()
            return ["mustering_started"]
        game.start()
        return ["game_start", "phase_started"]

    def events_for(self, game):
        return self.started_events

    def event_kwargs(self, event, game):
        if event == "phase_started":
            return {"phase": legacy_phase(game.current_phase)}
        return {"game": legacy_game(game)}


class CreateGame(StartingGameCommand):
    def perform(self, target):
        as_game_master = self.data.pop("game_master")
        variant = Variant.objects.get(pk=self.data.pop("variant_id"))
        game = GameBuilder.from_template(
            variant,
            seats=[{"user": self.actor, "kind": MemberKind.GAME_MASTER if as_game_master else MemberKind.PLAYER}],
            created_by=self.actor,
            admin=self.actor,
            game_master=self.actor if as_game_master else None,
            **self.data,
        )
        self.started_events = self.start_when_full(game)
        return game


class CreateSandboxGame(StartingGameCommand):
    def perform(self, target):
        variant = Variant.objects.get(pk=self.data["variant_id"])
        game = GameBuilder.from_template(
            variant,
            seats=[{"user": self.actor} for nation in variant.nations.all() if not nation.non_playable],
            name=self.data["name"],
            sandbox=True,
            private=True,
            movement_phase_duration=None,
        )
        self.started_events = self.start_when_full(game)
        return game


class CloneGameToSandbox(StartingGameCommand):
    decision = "can_clone_to_sandbox"

    def perform(self, source):
        sandboxes = list(Game.objects.filter(sandbox=True, members__user=self.actor).distinct().order_by("created_at"))
        if len(sandboxes) >= SANDBOX_LIMIT:
            delete_game(sandboxes[0])
        game = GameBuilder.from_phase(
            source.current_phase,
            seats=[{"user": self.actor} for nation in source.playable_nations],
            name=f"{source.name} (Sandbox)",
            sandbox=True,
            private=True,
            movement_phase_duration=None,
        )
        self.started_events = self.start_when_full(game)
        return game


class PauseGame(GameCommand):
    decision = "can_pause"
    events = ["game_paused"]

    def perform(self, game):
        game.pause()
        game.current_phase.sync_timers()
        return game


class UnpauseGame(GameCommand):
    decision = "can_unpause"
    events = ["game_resumed"]

    def perform(self, game):
        game.unpause()
        game.current_phase.sync_timers()
        return game


class ExtendGameDeadline(GameCommand):
    decision = "can_extend_deadline"
    events = ["game_deadline_extended"]

    def perform(self, game):
        game.extend_deadline(self.data["duration"])
        return game


class DeleteGame(GameCommand):
    decision = "can_delete"

    def perform(self, game):
        self.notify = not game.sandbox
        self.recipients = list(game.seated_user_ids)
        self.game_name = game.name
        delete_game(game)
        return game

    def events_for(self, game):
        return ["game_deleted"] if self.notify else []

    def event_kwargs(self, event, game):
        return {"recipients": self.recipients, "game_name": self.game_name, "actor": self.actor}


class StartMusteredGame(GameCommand):
    def applies(self, game):
        if game.status != GameStatus.MUSTERING:
            return False
        return game.is_mustered or (game.muster_deadline is not None and game.muster_deadline <= timezone.now())

    def perform(self, game):
        self.no_shows = game.unmustered_players
        self.no_show_user_ids = {member.user_id for member in self.no_shows if member.user_id is not None}
        game.start()
        for member in self.no_shows:
            member.remove()
            record_commitment(member, CommitmentEvent.MUSTER_NO_SHOW)
        game.current_phase.sync_timers()
        return game

    def events_for(self, game):
        events = ["game_start", "phase_started"]
        return events + ["removed_from_muster"] if self.no_show_user_ids else events

    def event_kwargs(self, event, game):
        if event == "phase_started":
            return {"phase": legacy_phase(game.current_phase)}
        if event == "game_start":
            return {"game": legacy_game(game), "recipients": list(game.seated_user_ids - self.no_show_user_ids)}
        return {"game": legacy_game(game), "recipients": list(self.no_show_user_ids)}


class SendMusterReminder(GameCommand):
    def applies(self, game):
        reminder_at = game.muster_reminder_at
        return (
            Game.objects.musterable().filter(pk=game.pk).exists()
            and game.muster_deadline > timezone.now()
            and reminder_at <= timezone.now()
        )

    def perform(self, game):
        self.recipients = [member.user_id for member in game.unmustered_players]
        return game

    def events_for(self, game):
        return ["muster_reminder"] if self.recipients else []

    def event_kwargs(self, event, game):
        return {"game": legacy_game(game), "recipients": self.recipients}
