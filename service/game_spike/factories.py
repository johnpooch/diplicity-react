import json
from pathlib import Path
from unittest.mock import patch

import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

from common.constants import Commitment, DeadlineMode, MemberKind, MovementPhaseDuration, UserKind
from user_profile.models import UserProfile
from variant.models import Variant

from .builders import GameBuilder
from .models import Game, Order, PhaseState, Victory

CLASSICAL_START = json.loads(
    (Path(__file__).resolve().parent.parent / "game" / "tests" / "data" / "start_classical.json").read_text()
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"spike-user-{n}")
    email = factory.LazyAttribute(lambda user: f"{user.username}@example.com")

    @factory.post_generation
    def profile(user, create, extracted, **kwargs):
        UserProfile.objects.create(
            user=user,
            name=kwargs.get("name", user.username),
            commitment=kwargs.get("commitment", Commitment.UNDEFINED),
            kind=kwargs.get("kind", UserKind.HUMAN),
        )


def _seats(game):
    nation_count = len([nation for nation in game.variant.nations.all() if not nation.non_playable])
    creator = {"user": game.created_by, "kind": MemberKind.GAME_MASTER if game.as_game_master else MemberKind.PLAYER}
    if game.sandbox:
        return [{"user": game.created_by} for _ in range(nation_count)]
    players = game.players if isinstance(game.players, list) else [UserFactory() for _ in range(game.players)]
    seats = [creator] + [{"user": user} for user in players]
    if game.full:
        seats += [{"user": UserFactory()} for _ in range(nation_count - len(seats) + int(game.as_game_master))]
    return seats


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game
        skip_postgeneration_save = True

    class Params:
        players = 0
        full = False
        as_game_master = False
        active = factory.Trait(full=True, started=True)
        mustering = factory.Trait(full=True, muster_required=True, mustering_entered=True)
        paused = factory.Trait(full=True, started=True, paused_now=True)
        completed = factory.Trait(full=True, started=True, completed_now=True)
        sandboxed = factory.Trait(sandbox=True, private=True, movement_phase_duration=None, started=True)

    name = factory.Sequence(lambda n: f"Spike Game {n}")
    variant = factory.LazyFunction(lambda: Variant.objects.get(id="classical"))
    created_by = factory.SubFactory(UserFactory)
    admin = factory.SelfAttribute("created_by")
    game_master = factory.LazyAttribute(lambda game: game.created_by if game.as_game_master else None)
    private = factory.LazyAttribute(lambda game: game.as_game_master)
    sandbox = False
    deadline_mode = DeadlineMode.DURATION
    movement_phase_duration = MovementPhaseDuration.TWENTY_FOUR_HOURS
    seats = factory.LazyAttribute(_seats)

    mustering_entered = False
    mustered = ()
    muster_ends_in = None
    started = False
    orders_submitted_by = ()
    orders_confirmed_by = ()
    paused_now = False
    completed_now = False
    won_by = ()

    @classmethod
    def _create(
        cls,
        model_class,
        variant,
        seats,
        mustering_entered,
        mustered,
        muster_ends_in,
        started,
        orders_submitted_by,
        orders_confirmed_by,
        paused_now,
        completed_now,
        won_by,
        **fields,
    ):
        game = GameBuilder.from_template(variant, seats=seats, **fields)
        if mustering_entered:
            game.enter_mustering()
        if mustered:
            seats = game.members.all() if mustered is True else game.members.filter(user__in=mustered)
            seats.update(mustered_at=timezone.now())
            game.sync_timers()
        if muster_ends_in is not None:
            game.muster_deadline = timezone.now() + muster_ends_in
            game.save(update_fields=["muster_deadline"])
        if started:
            with patch("adjudicator.service.start", return_value=CLASSICAL_START):
                game.start()
        for state in PhaseState.objects.filter(member__game=game, member__user__in=orders_submitted_by):
            Order.objects.create(phase_state=state)
        PhaseState.objects.filter(member__game=game, member__user__in=orders_confirmed_by).update(orders_confirmed=True)
        if paused_now:
            game.pause()
        if completed_now:
            game.complete()
        if won_by:
            victory = Victory.objects.create(game=game, winning_phase=game.phases.last())
            victory.members.set(game.members.filter(user__in=won_by))
        return game
