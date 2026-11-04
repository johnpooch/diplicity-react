import pytest
from django.utils import timezone

from rating.calculation import Player
from rating.models import RatingPairing, RatingResult


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
