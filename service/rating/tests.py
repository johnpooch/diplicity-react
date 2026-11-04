import pytest
from django.db import IntegrityError

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
