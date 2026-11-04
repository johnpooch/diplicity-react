import pytest
from django.utils import timezone

from common.constants import GameStatus, PhaseStatus, PhaseType
from game.models import Game
from nation.models import Nation
from rating.calculation import Player
from rating.models import RatingPairing, RatingResult
from victory.models import Victory


@pytest.fixture
def rating_result_factory(db, member_factory):
    def _create(member=None, **kwargs):
        if member is None:
            member = member_factory()
        values = {
            "rating_before": 1500,
            "deviation_before": 350,
            "rating_after": 1531,
            "deviation_after": 310,
            "handicap": 0,
        }
        values.update(kwargs)
        return RatingResult.objects.create(member=member, **values)

    return _create


@pytest.fixture
def rating_pairing_factory(db, rating_result_factory, member_factory):
    def _create(result=None, opponent=None, **kwargs):
        if result is None:
            result = rating_result_factory()
        if opponent is None:
            opponent = member_factory(game=result.member.game)
        values = {
            "opponent_rating": 1500,
            "opponent_deviation": 350,
            "opponent_handicap": 0,
            "score": 1,
            "change": 31,
        }
        values.update(kwargs)
        return RatingPairing.objects.create(result=result, opponent=opponent, **values)

    return _create


@pytest.fixture
def rated_at():
    return timezone.now()


@pytest.fixture
def player_factory(rated_at):
    def _create(member_id, victor=False, **kwargs):
        values = {
            "seat": member_id,
            "rating": 1500,
            "deviation": 100,
            "rated_at": rated_at,
            "handicap": 0,
        }
        values.update(kwargs)
        return Player(member_id=member_id, victor=victor, **values)

    return _create


@pytest.fixture
def unhandicapped_nation(db):
    return Nation.objects.get(variant_id="vietnam-war", name="Laos")


@pytest.fixture
def ranked_game_factory(db, classical_variant, member_factory):
    def _create(victors=1, last_year=1903, **kwargs):
        values = {"status": GameStatus.COMPLETED, "ranked": True}
        values.update(kwargs)
        game = Game.objects.create(
            variant=classical_variant,
            name=f"Ranked Game {Game.objects.count()}",
            **values,
        )
        game.phases.create(
            variant=classical_variant,
            season="Spring",
            year=1901,
            type=PhaseType.MOVEMENT,
            status=PhaseStatus.COMPLETED,
            ordinal=1,
        )
        last_phase = game.phases.create(
            variant=classical_variant,
            season="Spring",
            year=last_year,
            type=PhaseType.MOVEMENT,
            status=PhaseStatus.COMPLETED,
            ordinal=2,
        )
        members = [
            member_factory(game=game, nation=nation)
            for nation in classical_variant.nations.filter(non_playable=False)
        ]
        victory = Victory.objects.create(game=game, winning_phase=last_phase)
        victory.members.set(members[:victors])
        return game

    return _create
