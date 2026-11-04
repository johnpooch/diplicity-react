from datetime import timedelta

import pytest
from django.db import IntegrityError

from rating.calculation import (
    DEFAULT_PARAMETERS,
    Match,
    Parameters,
    grown_deviation,
    rate,
    update,
)
from rating.models import NationHandicap, Rating


class TestGameRanked:
    @pytest.mark.django_db
    def test_game_is_not_ranked_by_default(self, game_factory):
        game = game_factory()

        game.refresh_from_db()
        assert game.ranked is False


class TestRating:
    @pytest.mark.django_db
    def test_one_rating_per_user(self, user_factory, rated_at):
        user = user_factory()
        Rating.objects.create(user=user, rating=1500, deviation=350, rated_at=rated_at)

        with pytest.raises(IntegrityError):
            Rating.objects.create(
                user=user, rating=1500, deviation=350, rated_at=rated_at
            )


class TestRatingResult:
    @pytest.mark.django_db
    def test_one_result_per_member(self, rating_result_factory):
        result = rating_result_factory()

        with pytest.raises(IntegrityError):
            rating_result_factory(member=result.member)

    @pytest.mark.django_db
    def test_result_is_not_protected_by_default(self, rating_result_factory):
        result = rating_result_factory()

        result.refresh_from_db()
        assert result.protected is False


class TestRatingPairing:
    @pytest.mark.django_db
    def test_pairings_belong_to_result(
        self, rating_result_factory, rating_pairing_factory
    ):
        result = rating_result_factory()
        first = rating_pairing_factory(result=result)
        second = rating_pairing_factory(result=result, score=0.5, change=0)

        assert set(result.pairings.all()) == {first, second}

    @pytest.mark.django_db
    def test_one_pairing_per_opponent(self, rating_pairing_factory):
        pairing = rating_pairing_factory()

        with pytest.raises(IntegrityError):
            rating_pairing_factory(result=pairing.result, opponent=pairing.opponent)


class TestNationHandicap:
    @pytest.mark.django_db
    def test_one_handicap_per_nation(self, classical_england_nation):
        NationHandicap.objects.create(nation=classical_england_nation, offset=-20)

        with pytest.raises(IntegrityError):
            NationHandicap.objects.create(nation=classical_england_nation, offset=10)


class TestNationHandicapAdmin:
    @pytest.fixture
    def admin_client(self, client, user_factory):
        user = user_factory(username="handicap_admin")
        user.is_staff = True
        user.is_superuser = True
        user.save()
        client.force_login(user)
        return client

    @pytest.mark.django_db
    def test_superuser_adds_handicap(self, admin_client, classical_england_nation):
        response = admin_client.post(
            "/admin/rating/nationhandicap/add/",
            {"nation": classical_england_nation.id, "offset": -25},
        )

        assert response.status_code == 302
        assert NationHandicap.objects.get(nation=classical_england_nation).offset == -25

    @pytest.mark.django_db
    def test_superuser_lists_handicaps(self, admin_client, classical_england_nation):
        NationHandicap.objects.create(nation=classical_england_nation, offset=-25)

        response = admin_client.get("/admin/rating/nationhandicap/")

        assert response.status_code == 200
        assert "England" in response.content.decode()


def _by_member(results):
    return {result.member_id: result for result in results}


def _scores(result):
    return {pairing.opponent_id: pairing.score for pairing in result.pairings}


class TestGrownDeviation:
    def test_unchanged_when_just_rated(self, rated_at):
        assert grown_deviation(80, rated_at, rated_at) == 80

    def test_grows_with_time_since_rated(self, rated_at):
        later = rated_at + DEFAULT_PARAMETERS.period * 4

        assert grown_deviation(80, rated_at, later) == pytest.approx(
            (80**2 + DEFAULT_PARAMETERS.volatility**2 * 4) ** 0.5
        )

    def test_settled_deviation_returns_to_max_after_return_period(self, rated_at):
        later = rated_at + DEFAULT_PARAMETERS.return_to_max

        assert grown_deviation(50, rated_at, later) == pytest.approx(350)

    def test_capped_at_max(self, rated_at):
        later = rated_at + timedelta(days=3650)

        assert grown_deviation(50, rated_at, later) == 350


class TestUpdate:
    def test_matches_glickman_example(self):
        deviation, changes = update(
            1500,
            200,
            [
                Match(rating=1400, deviation=30, score=1, weight=1),
                Match(rating=1550, deviation=100, score=0, weight=1),
                Match(rating=1700, deviation=300, score=0, weight=1),
            ],
        )

        assert 1500 + sum(changes) == pytest.approx(1464.1, abs=0.1)
        assert deviation == pytest.approx(151.4, abs=0.1)

    def test_no_matches_changes_nothing(self):
        assert update(1500, 200, []) == (200, [])


class TestRatePairings:
    def test_solo_winner_beats_everyone(self, player_factory, rated_at):
        players = [player_factory(1, victor=True), player_factory(2), player_factory(3)]

        results = _by_member(rate(players, rated_at))

        assert _scores(results[1]) == {2: 1, 3: 1}
        assert _scores(results[2]) == {1: 0}
        assert _scores(results[3]) == {1: 0}

    def test_drawers_tie_each_other_and_beat_the_rest(self, player_factory, rated_at):
        players = [
            player_factory(1, victor=True),
            player_factory(2, victor=True),
            player_factory(3),
            player_factory(4),
        ]

        results = _by_member(rate(players, rated_at))

        assert _scores(results[1]) == {2: 0.5, 3: 1, 4: 1}
        assert _scores(results[2]) == {1: 0.5, 3: 1, 4: 1}
        assert _scores(results[3]) == {1: 0, 2: 0}
        assert _scores(results[4]) == {1: 0, 2: 0}

    def test_departed_player_loses_to_other_seats_final_occupants(
        self, player_factory, rated_at
    ):
        players = [
            player_factory(1, victor=True),
            player_factory(2, seat=10, departed=True),
            player_factory(3, seat=10, replacement=True),
            player_factory(4),
        ]

        results = _by_member(rate(players, rated_at))

        assert _scores(results[2]) == {1: 0, 4: 0}
        assert _scores(results[1]) == {3: 1, 4: 1}
        assert _scores(results[3]) == {1: 0}
        assert _scores(results[4]) == {1: 0}

    def test_pairings_snapshot_opponent(self, player_factory, rated_at):
        players = [
            player_factory(1, victor=True),
            player_factory(2, rating=1620, deviation=50, handicap=-15),
        ]
        later = rated_at + DEFAULT_PARAMETERS.period * 6

        pairing = _by_member(rate(players, later))[1].pairings[0]

        assert pairing.opponent_rating == 1620
        assert pairing.opponent_deviation == grown_deviation(50, rated_at, later)
        assert pairing.opponent_handicap == -15


class TestRateChanges:
    def test_single_seat_game_changes_nothing(self, player_factory, rated_at):
        result = rate([player_factory(1, victor=True)], rated_at)[0]

        assert result.pairings == ()
        assert result.rating_after == result.rating_before
        assert result.deviation_after == result.deviation_before

    def test_winner_gains_and_losers_lose(self, player_factory, rated_at):
        players = [player_factory(1, victor=True), player_factory(2), player_factory(3)]

        results = _by_member(rate(players, rated_at))

        assert results[1].rating_after > 1500
        assert results[2].rating_after < 1500
        assert results[3].rating_after < 1500

    def test_breakdown_adds_up_to_total_change(self, player_factory, rated_at):
        players = [
            player_factory(1, victor=True, rating=1450),
            player_factory(2, victor=True, rating=1580, handicap=20),
            player_factory(3, rating=1700, deviation=60),
            player_factory(4, rating=1300, deviation=300),
        ]

        for result in rate(players, rated_at):
            assert result.rating_after - result.rating_before == pytest.approx(
                sum(pairing.change for pairing in result.pairings)
            )

    def test_deviation_shrinks_after_a_game(self, player_factory, rated_at):
        players = [player_factory(1, victor=True), player_factory(2)]

        for result in rate(players, rated_at):
            assert result.deviation_after < result.deviation_before

    def test_deviation_grows_before_the_update(self, player_factory, rated_at):
        players = [player_factory(1, victor=True), player_factory(2)]
        later = rated_at + DEFAULT_PARAMETERS.period * 12

        result = _by_member(rate(players, later))[1]

        assert result.deviation_before == grown_deviation(100, rated_at, later)

    def test_weak_nation_gains_more_for_a_win(self, player_factory, rated_at):
        even = [player_factory(1, victor=True), player_factory(2)]
        weak = [player_factory(1, victor=True, handicap=-50), player_factory(2)]

        even_result = _by_member(rate(even, rated_at))[1]
        weak_result = _by_member(rate(weak, rated_at))[1]

        assert weak_result.rating_after > even_result.rating_after
        assert weak_result.handicap == -50

    def test_two_player_game_is_one_full_match(self, player_factory, rated_at):
        players = [player_factory(1, victor=True), player_factory(2, rating=1600)]

        result = _by_member(rate(players, rated_at))[1]
        deviation, changes = update(
            1500, 100, [Match(rating=1600, deviation=100, score=1, weight=1)]
        )

        assert result.rating_after == pytest.approx(1500 + sum(changes))
        assert result.deviation_after == pytest.approx(deviation)

    def test_pairings_are_weighted_by_seat_count(self, player_factory, rated_at):
        players = [player_factory(1, victor=True)] + [
            player_factory(member_id) for member_id in range(2, 8)
        ]

        result = _by_member(rate(players, rated_at))[1]
        deviation, changes = update(
            1500,
            100,
            [Match(rating=1500, deviation=100, score=1, weight=1 / 6)] * 6,
        )

        assert result.rating_after == pytest.approx(1500 + sum(changes))
        assert result.deviation_after == pytest.approx(deviation)

    def test_weight_scale_is_a_parameter(self, player_factory, rated_at):
        players = [player_factory(1, victor=True), player_factory(2), player_factory(3)]

        default = _by_member(rate(players, rated_at))[1]
        doubled = _by_member(rate(players, rated_at, Parameters(weight_scale=2)))[1]

        assert doubled.rating_after > default.rating_after


class TestRateReplacements:
    def test_negative_replacement_result_is_protected(self, player_factory, rated_at):
        players = [
            player_factory(1, victor=True),
            player_factory(2, seat=10, departed=True),
            player_factory(3, seat=10, replacement=True),
        ]

        result = _by_member(rate(players, rated_at))[3]

        assert result.protected is True
        assert result.rating_after == result.rating_before
        assert result.deviation_after == result.deviation_before
        assert result.pairings[0].change < 0

    def test_positive_replacement_result_counts(self, player_factory, rated_at):
        players = [
            player_factory(1, seat=10, departed=True),
            player_factory(2, seat=10, victor=True, replacement=True),
            player_factory(3),
        ]

        result = _by_member(rate(players, rated_at))[2]

        assert result.protected is False
        assert result.rating_after > result.rating_before

    def test_departed_player_is_not_protected(self, player_factory, rated_at):
        players = [
            player_factory(1, victor=True),
            player_factory(2, seat=10, departed=True),
            player_factory(3, seat=10, replacement=True),
        ]

        result = _by_member(rate(players, rated_at))[2]

        assert result.protected is False
        assert result.rating_after < result.rating_before
