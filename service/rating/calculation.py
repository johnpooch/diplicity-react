import math
from dataclasses import dataclass
from datetime import datetime, timedelta

Q = math.log(10) / 400


@dataclass(frozen=True)
class Parameters:
    max_deviation: float = 350
    settled_deviation: float = 50
    return_to_max: timedelta = timedelta(days=730)
    period: timedelta = timedelta(days=30)
    weight_scale: float = 1

    @property
    def volatility(self):
        periods = self.return_to_max / self.period
        return math.sqrt((self.max_deviation**2 - self.settled_deviation**2) / periods)

    def weight(self, seats):
        return self.weight_scale / (seats - 1)


DEFAULT_PARAMETERS = Parameters()


@dataclass(frozen=True)
class Player:
    member_id: int
    seat: int
    rating: float
    deviation: float
    rated_at: datetime
    handicap: int
    victor: bool
    departed: bool = False
    replacement: bool = False


@dataclass(frozen=True)
class Match:
    rating: float
    deviation: float
    score: float
    weight: float


@dataclass(frozen=True)
class Pairing:
    opponent_id: int
    opponent_rating: float
    opponent_deviation: float
    opponent_handicap: int
    score: float
    change: float


@dataclass(frozen=True)
class Result:
    member_id: int
    rating_before: float
    deviation_before: float
    rating_after: float
    deviation_after: float
    handicap: int
    protected: bool
    pairings: tuple


def grown_deviation(deviation, rated_at, now, parameters=DEFAULT_PARAMETERS):
    periods = max(now - rated_at, timedelta(0)) / parameters.period
    return min(
        math.sqrt(deviation**2 + parameters.volatility**2 * periods),
        parameters.max_deviation,
    )


def _g(deviation):
    return 1 / math.sqrt(1 + 3 * Q**2 * deviation**2 / math.pi**2)


def _expected_score(rating, opponent_rating, opponent_deviation):
    return 1 / (1 + 10 ** (-_g(opponent_deviation) * (rating - opponent_rating) / 400))


def update(rating, deviation, matches):
    inverse_d_squared = Q**2 * sum(
        match.weight
        * _g(match.deviation) ** 2
        * _expected_score(rating, match.rating, match.deviation)
        * (1 - _expected_score(rating, match.rating, match.deviation))
        for match in matches
    )
    new_variance = 1 / (1 / deviation**2 + inverse_d_squared)
    changes = [
        Q
        * new_variance
        * match.weight
        * _g(match.deviation)
        * (match.score - _expected_score(rating, match.rating, match.deviation))
        for match in matches
    ]
    return math.sqrt(new_variance), changes


def _opponents(player, players):
    final_occupants = [other for other in players if not other.departed]
    if player.departed:
        return [(other, 0) for other in final_occupants if other.seat != player.seat]
    if player.victor:
        return [
            (other, 0.5 if other.victor else 1)
            for other in final_occupants
            if other.member_id != player.member_id
        ]
    return [(other, 0) for other in final_occupants if other.victor]


def rate(players, now, parameters=DEFAULT_PARAMETERS):
    deviations = {
        player.member_id: grown_deviation(
            player.deviation, player.rated_at, now, parameters
        )
        for player in players
    }
    seats = len({player.seat for player in players})
    weight = parameters.weight(seats) if seats > 1 else 0
    return [_rate_player(player, players, deviations, weight) for player in players]


def _rate_player(player, players, deviations, weight):
    paired = _opponents(player, players)
    deviation = deviations[player.member_id]
    new_deviation, changes = update(
        player.rating + player.handicap,
        deviation,
        [
            Match(
                rating=opponent.rating + opponent.handicap,
                deviation=deviations[opponent.member_id],
                score=score,
                weight=weight,
            )
            for opponent, score in paired
        ],
    )
    change = sum(changes)
    protected = player.replacement and change < 0
    return Result(
        member_id=player.member_id,
        rating_before=player.rating,
        deviation_before=deviation,
        rating_after=player.rating if protected else player.rating + change,
        deviation_after=deviation if protected else new_deviation,
        handicap=player.handicap,
        protected=protected,
        pairings=tuple(
            Pairing(
                opponent_id=opponent.member_id,
                opponent_rating=opponent.rating,
                opponent_deviation=deviations[opponent.member_id],
                opponent_handicap=opponent.handicap,
                score=score,
                change=pairing_change,
            )
            for (opponent, score), pairing_change in zip(paired, changes)
        ),
    )
