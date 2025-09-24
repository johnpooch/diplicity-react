import pytest
from game import models
from django.db import connection
from django.contrib.auth import get_user_model
from user_profile.models import UserProfile
from variant.models import Variant

User = get_user_model()


@pytest.mark.django_db
def test_game_queryset_with_variant(django_assert_num_queries):
    """
    Test that the GameQuerySet.with_variant() method returns a queryset with the
    variant selected. Accessing iterating over the queryset and accessing the
    variant should not result in additional queries.
    """
    variant_a = Variant.objects.get(id="classical")
    variant_b = Variant.objects.get(id="italy-vs-germany")
    game_a = models.Game.objects.create(name="Game A", variant=variant_a)
    game_b = models.Game.objects.create(name="Game B", variant=variant_b)

    connection.queries_log.clear()

    queryset = models.Game.objects.get_queryset().with_variant()

    with django_assert_num_queries(1):
        games = list(queryset)
        for game in games:
            _ = game.variant.name


@pytest.mark.django_db
def test_game_queryset_with_phases(django_assert_num_queries):
    """
    Test that the GameQuerySet.with_supply_centers() method returns a queryset with the
    phases and supply centers selected. Iterating over the queryset and accessing the
    supply centers should not result in additional queries.
    """
    variant_a = Variant.objects.get(id="classical")
    variant_b = Variant.objects.get(id="italy-vs-germany")

    game_a = models.Game.objects.create(name="Game A", variant=variant_a)
    game_b = models.Game.objects.create(name="Game B", variant=variant_b)

    game_a_phase_1 = game_a.phases.create(
        ordinal=1, season="Spring", year=1901, type="Movement"
    )
    game_a_phase_2 = game_a.phases.create(
        ordinal=2, season="Fall", year=1901, type="Movement"
    )
    game_b_phase_1 = game_b.phases.create(
        ordinal=1, season="Spring", year=1902, type="Movement"
    )
    game_b_phase_2 = game_b.phases.create(
        ordinal=2, season="Fall", year=1902, type="Movement"
    )

    game_a_phase_1.supply_centers.create(province="A", nation="A")
    game_a_phase_2.supply_centers.create(province="B", nation="B")
    game_b_phase_1.supply_centers.create(province="C", nation="C")
    game_b_phase_2.supply_centers.create(province="D", nation="D")

    game_a_phase_1.units.create(type=models.Unit.ARMY, nation="A", province="A")
    game_a_phase_2.units.create(type=models.Unit.ARMY, nation="B", province="B")
    game_b_phase_1.units.create(type=models.Unit.ARMY, nation="C", province="C")
    game_b_phase_2.units.create(type=models.Unit.ARMY, nation="D", province="D")

    connection.queries_log.clear()

    queryset = models.Game.objects.get_queryset().with_phases()

    with django_assert_num_queries(5):
        games = list(queryset)


@pytest.mark.django_db
def test_game_queryset_with_members(django_assert_num_queries):
    """
    Test that the GameQuerySet.with_members() method returns a queryset with the
    members and their user profiles selected. Iterating over the queryset and accessing the
    members and their user profiles should not result in additional queries.
    """
    variant_a = Variant.objects.get(id="classical")
    variant_b = Variant.objects.get(id="italy-vs-germany")

    game_a = models.Game.objects.create(name="Game A", variant=variant_a)
    game_b = models.Game.objects.create(name="Game B", variant=variant_b)

    user_1 = User.objects.create_user(username="user1", email="user1@example.com")
    user_2 = User.objects.create_user(username="user2", email="user2@example.com")
    user_3 = User.objects.create_user(username="user3", email="user3@example.com")

    profile_1 = UserProfile.objects.create(
        user=user_1, name="User One", picture="http://example.com/1.jpg"
    )
    profile_2 = UserProfile.objects.create(
        user=user_2, name="User Two", picture="http://example.com/2.jpg"
    )
    profile_3 = UserProfile.objects.create(
        user=user_3, name="User Three", picture="http://example.com/3.jpg"
    )

    game_a.members.create(user=user_1, nation="England")
    game_a.members.create(user=user_2, nation="France")
    game_b.members.create(user=user_3, nation="Germany")

    connection.queries_log.clear()

    queryset = models.Game.objects.get_queryset().with_members()

    with django_assert_num_queries(4):
        games = list(queryset)
        for game in games:
            for member in game.members.all():
                _ = member.user.profile.name


@pytest.mark.django_db
def test_game_queryset_includes_user(django_assert_num_queries):
    """
    Test that the GameQuerySet.includes_user() method returns only games that
    include the specified user as a member.
    """
    variant_a = Variant.objects.get(id="classical")
    variant_b = Variant.objects.get(id="italy-vs-germany")

    game_a = models.Game.objects.create(name="Game A", variant=variant_a)
    game_b = models.Game.objects.create(name="Game B", variant=variant_b)

    user_1 = User.objects.create_user(username="user1", email="user1@example.com")
    user_2 = User.objects.create_user(username="user2", email="user2@example.com")

    game_a.members.create(user=user_1, nation="England")
    game_a.members.create(user=user_2, nation="France")
    game_b.members.create(user=user_2, nation="Germany")

    connection.queries_log.clear()

    queryset = models.Game.objects.get_queryset().includes_user(user_1)

    with django_assert_num_queries(1):
        games = list(queryset)
        assert len(games) == 1
        assert games[0].name == "Game A"
