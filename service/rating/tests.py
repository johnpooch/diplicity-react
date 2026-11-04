import importlib
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.apps import apps
from django.db import IntegrityError
from django.utils import timezone

from common.constants import GameStatus, PhaseType, RatingJob
from nation.models import Nation
from phase.models import Phase

from rating.calculation import (
    DEFAULT_PARAMETERS,
    Match,
    Parameters,
    grown_deviation,
    rate,
    update,
)
from rating.models import NationHandicap, Rating, RatingPairing, RatingResult
from rating.tasks import rate_game
from victory.models import Victory

seed_handicaps_migration = importlib.import_module(
    "rating.migrations.0002_seed_nation_handicaps"
)


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
    def test_one_handicap_per_nation(self, unhandicapped_nation):
        NationHandicap.objects.create(nation=unhandicapped_nation, offset=-20)

        with pytest.raises(IntegrityError):
            NationHandicap.objects.create(nation=unhandicapped_nation, offset=10)


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
    def test_superuser_adds_handicap(self, admin_client, unhandicapped_nation):
        response = admin_client.post(
            "/admin/rating/nationhandicap/add/",
            {"nation": unhandicapped_nation.id, "offset": -25},
        )

        assert response.status_code == 302
        assert NationHandicap.objects.get(nation=unhandicapped_nation).offset == -25

    @pytest.mark.django_db
    def test_superuser_lists_handicaps(self, admin_client):
        response = admin_client.get("/admin/rating/nationhandicap/")

        assert response.status_code == 200
        assert "England" in response.content.decode()


class TestSeedNationHandicaps:
    def _offsets(self, variant_id):
        return dict(
            NationHandicap.objects.filter(nation__variant_id=variant_id).values_list(
                "nation__name", "offset"
            )
        )

    @pytest.mark.django_db
    def test_seeds_every_playable_nation_of_present_variants(self):
        for variant_id, offsets in seed_handicaps_migration.HANDICAPS.items():
            if Nation.objects.filter(variant_id=variant_id).exists():
                assert self._offsets(variant_id) == offsets

    @pytest.mark.django_db
    def test_seeds_classical(self):
        assert self._offsets("classical") == {
            "France": 25,
            "Turkey": 21,
            "England": 15,
            "Germany": -3,
            "Russia": -11,
            "Italy": -17,
            "Austria": -30,
        }

    @pytest.mark.django_db
    def test_leaves_unlisted_variants_without_handicaps(self):
        assert self._offsets("vietnam-war") == {}

    @pytest.mark.django_db
    def test_seed_is_idempotent(self):
        NationHandicap.objects.filter(nation__variant_id="classical").update(offset=0)

        seed_handicaps_migration.seed(apps, None)

        assert self._offsets("classical")["France"] == 25

    @pytest.mark.django_db
    def test_seed_refuses_mismatched_nations(self):
        Nation.objects.filter(variant_id="classical", name="France").update(name="Gaul")

        with pytest.raises(ValueError):
            seed_handicaps_migration.seed(apps, None)

    @pytest.mark.django_db
    def test_unseed_removes_seeded_handicaps(self, unhandicapped_nation):
        NationHandicap.objects.create(nation=unhandicapped_nation, offset=5)

        seed_handicaps_migration.unseed(apps, None)

        assert list(NationHandicap.objects.values_list("nation", flat=True)) == [
            unhandicapped_nation.id
        ]


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

    def test_two_player_game_is_weighted_by_scale(self, player_factory, rated_at):
        players = [player_factory(1, victor=True), player_factory(2, rating=1600)]

        result = _by_member(rate(players, rated_at))[1]
        deviation, changes = update(
            1500, 100, [Match(rating=1600, deviation=100, score=1, weight=2)]
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
            [Match(rating=1500, deviation=100, score=1, weight=2 / 6)] * 6,
        )

        assert result.rating_after == pytest.approx(1500 + sum(changes))
        assert result.deviation_after == pytest.approx(deviation)

    def test_weight_scale_is_a_parameter(self, player_factory, rated_at):
        players = [player_factory(1, victor=True), player_factory(2), player_factory(3)]

        default = _by_member(rate(players, rated_at))[1]
        doubled = _by_member(rate(players, rated_at, Parameters(weight_scale=4)))[1]

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


def _replace(member, user_factory):
    replacement = member.game.members.create(user=user_factory())
    member.removed_at = timezone.now()
    member.replaced_by = replacement
    member.save(update_fields=["removed_at", "replaced_by"])
    replacement.nation = member.nation
    replacement.save(update_fields=["nation"])
    return replacement


def _victors(game):
    return list(game.victory.members.all())


def _losers(game):
    victors = _victors(game)
    return [member for member in game.members.all() if member not in victors]


def _rating_jobs(connector):
    return [
        job
        for job in connector.jobs.values()
        if job["task_name"] == RatingJob.TASK_NAME
    ]


class TestRateGame:
    @pytest.mark.django_db
    def test_records_a_result_for_every_player(self, ranked_game_factory):
        game = ranked_game_factory()

        RatingResult.objects.rate_game(game)

        assert RatingResult.objects.filter(member__game=game).count() == 7

    @pytest.mark.django_db
    def test_solo_winner_is_paired_with_every_other_player(self, ranked_game_factory):
        game = ranked_game_factory()
        [winner] = _victors(game)

        RatingResult.objects.rate_game(game)

        assert (
            sorted(winner.rating_result.pairings.values_list("score", flat=True))
            == [1] * 6
        )

    @pytest.mark.django_db
    def test_losers_are_paired_only_with_the_winner(self, ranked_game_factory):
        game = ranked_game_factory()
        [winner] = _victors(game)

        RatingResult.objects.rate_game(game)

        for loser in _losers(game):
            assert list(
                loser.rating_result.pairings.values_list("opponent", "score")
            ) == [(winner.pk, 0)]

    @pytest.mark.django_db
    def test_drawers_tie_each_other(self, ranked_game_factory):
        game = ranked_game_factory(victors=2)
        first, second = _victors(game)

        RatingResult.objects.rate_game(game)

        assert first.rating_result.pairings.get(opponent=second).score == 0.5

    @pytest.mark.django_db
    def test_creates_ratings_for_new_players(self, ranked_game_factory):
        game = ranked_game_factory()
        [winner] = _victors(game)

        RatingResult.objects.rate_game(game)

        result = winner.rating_result
        rating = Rating.objects.get(user=winner.user)
        assert result.rating_before == 1500
        assert result.deviation_before == 350
        assert rating.rating == result.rating_after > 1500
        assert rating.deviation == result.deviation_after < 350
        assert rating.rated_at == result.created_at

    @pytest.mark.django_db
    def test_lowers_the_losers_ratings(self, ranked_game_factory):
        game = ranked_game_factory()

        RatingResult.objects.rate_game(game)

        for loser in _losers(game):
            assert Rating.objects.get(user=loser.user).rating < 1500

    @pytest.mark.django_db
    def test_rates_from_existing_ratings(self, ranked_game_factory):
        game = ranked_game_factory()
        [winner] = _victors(game)
        rated_at = timezone.now() - timedelta(days=30)
        Rating.objects.create(
            user=winner.user, rating=1700, deviation=80, rated_at=rated_at
        )

        RatingResult.objects.rate_game(game)

        result = winner.rating_result
        assert result.rating_before == 1700
        assert result.deviation_before == pytest.approx(
            grown_deviation(80, rated_at, result.created_at), abs=0.01
        )
        assert Rating.objects.get(user=winner.user).rating == result.rating_after

    @pytest.mark.django_db
    def test_copies_the_nation_handicaps(self, ranked_game_factory):
        game = ranked_game_factory()
        france = game.members.get(nation__name="France")

        RatingResult.objects.rate_game(game)

        assert france.rating_result.handicap == 25
        assert (
            RatingPairing.objects.filter(opponent=france).first().opponent_handicap
            == 25
        )

    @pytest.mark.django_db
    def test_pairing_changes_add_up_to_the_total_change(self, ranked_game_factory):
        game = ranked_game_factory(victors=3)

        RatingResult.objects.rate_game(game)

        for result in RatingResult.objects.filter(member__game=game):
            assert sum(
                result.pairings.values_list("change", flat=True)
            ) == pytest.approx(result.rating_after - result.rating_before)

    @pytest.mark.django_db
    def test_does_not_rate_bots(self, ranked_game_factory, bot_user):
        game = ranked_game_factory()
        bot = _losers(game)[0]
        bot.user = bot_user
        bot.save(update_fields=["user"])

        RatingResult.objects.rate_game(game)

        assert not RatingResult.objects.filter(member=bot).exists()
        assert not RatingPairing.objects.filter(opponent=bot).exists()
        assert not Rating.objects.filter(user=bot_user).exists()

    @pytest.mark.django_db
    def test_departed_player_loses_to_the_other_seats(
        self, ranked_game_factory, user_factory
    ):
        game = ranked_game_factory()
        departed = _losers(game)[0]
        replacement = _replace(departed, user_factory)

        RatingResult.objects.rate_game(game)

        opponents = set(
            departed.rating_result.pairings.values_list("opponent", flat=True)
        )
        assert replacement.pk not in opponents
        assert len(opponents) == 6
        assert set(departed.rating_result.pairings.values_list("score", flat=True)) == {
            0
        }

    @pytest.mark.django_db
    def test_losing_replacement_keeps_their_rating(
        self, ranked_game_factory, user_factory
    ):
        game = ranked_game_factory()
        replacement = _replace(_losers(game)[0], user_factory)
        rated_at = timezone.now() - timedelta(days=30)
        Rating.objects.create(
            user=replacement.user, rating=1600, deviation=100, rated_at=rated_at
        )

        RatingResult.objects.rate_game(game)

        result = replacement.rating_result
        rating = Rating.objects.get(user=replacement.user)
        assert result.protected
        assert result.rating_after == 1600
        assert result.pairings.get().change < 0
        assert (rating.rating, rating.deviation, rating.rated_at) == (
            1600,
            100,
            rated_at,
        )

    @pytest.mark.django_db
    def test_winning_replacement_gains(self, ranked_game_factory, user_factory):
        game = ranked_game_factory()
        replacement = _replace(_victors(game)[0], user_factory)
        game.victory.members.set([replacement])

        RatingResult.objects.rate_game(game)

        assert not replacement.rating_result.protected
        assert Rating.objects.get(user=replacement.user).rating > 1500

    @pytest.mark.django_db
    def test_returns_the_game(self, ranked_game_factory):
        game = ranked_game_factory()

        assert RatingResult.objects.rate_game(game) == game

    @pytest.mark.django_db
    def test_skips_unranked_games(self, ranked_game_factory):
        game = ranked_game_factory(ranked=False)

        assert RatingResult.objects.rate_game(game) is None
        assert not RatingResult.objects.exists()

    @pytest.mark.django_db
    def test_skips_games_that_are_not_completed(self, ranked_game_factory):
        game = ranked_game_factory(status=GameStatus.ABANDONED)

        assert RatingResult.objects.rate_game(game) is None
        assert not RatingResult.objects.exists()

    @pytest.mark.django_db
    def test_skips_games_shorter_than_two_years(self, ranked_game_factory):
        game = ranked_game_factory(last_year=1902)

        assert RatingResult.objects.rate_game(game) is None
        assert not RatingResult.objects.exists()

    @pytest.mark.django_db
    def test_does_not_rate_a_game_twice(self, ranked_game_factory):
        game = ranked_game_factory()
        [winner] = _victors(game)
        RatingResult.objects.rate_game(game)
        rating = Rating.objects.get(user=winner.user).rating

        assert RatingResult.objects.rate_game(game) is None
        assert RatingResult.objects.filter(member__game=game).count() == 7
        assert Rating.objects.get(user=winner.user).rating == rating


class TestRateGameTask:
    @pytest.mark.django_db
    def test_rates_the_game(self, ranked_game_factory):
        game = ranked_game_factory()

        rate_game(game_id=game.id)

        assert RatingResult.objects.filter(member__game=game).count() == 7


class TestRatingDeferredOnCompletion:
    @pytest.mark.django_db
    def test_draw_defers_rating(
        self,
        draw_notification_game_factory,
        in_memory_procrastinate,
        mock_immediate_on_commit,
    ):
        game, italy, germany = draw_notification_game_factory()

        game.finish_with_draw(game.current_phase, [italy, germany])

        [job] = _rating_jobs(in_memory_procrastinate)
        assert job["args"] == {"game_id": game.id}

    @pytest.mark.django_db
    def test_draw_defers_rating_only_after_commit(
        self, draw_notification_game_factory, in_memory_procrastinate
    ):
        game, italy, germany = draw_notification_game_factory()

        game.finish_with_draw(game.current_phase, [italy, germany])

        assert _rating_jobs(in_memory_procrastinate) == []

    @pytest.mark.django_db
    def test_solo_victory_defers_rating(
        self,
        draw_notification_game_factory,
        in_memory_procrastinate,
        mock_immediate_on_commit,
    ):
        game, italy, germany = draw_notification_game_factory()
        phase = game.current_phase
        adjudication_data = {
            "season": "Fall",
            "year": 1901,
            "type": PhaseType.MOVEMENT,
            "options": {},
            "supply_centers": [],
            "units": [],
            "resolutions": [],
        }

        with patch("phase.models.resolve", return_value=adjudication_data), patch(
            "phase.models.Victory.objects.try_create_victory",
            side_effect=lambda new_phase: Victory.objects.create(
                game=game, winning_phase=new_phase
            ),
        ):
            Phase.objects.resolve(phase)

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED
        [job] = _rating_jobs(in_memory_procrastinate)
        assert job["args"] == {"game_id": game.id}

    @pytest.mark.django_db
    def test_abandonment_does_not_defer_rating(
        self,
        draw_notification_game_factory,
        in_memory_procrastinate,
        mock_immediate_on_commit,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.members.update(civil_disorder_at=timezone.now())

        Phase.objects.resolve(game.current_phase)

        game.refresh_from_db()
        assert game.status == GameStatus.ABANDONED
        assert _rating_jobs(in_memory_procrastinate) == []
