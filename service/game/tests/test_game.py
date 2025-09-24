import pytest
from game import models
from django.db import connection
from django.contrib.auth import get_user_model
from user_profile.models import UserProfile
from variant.models import Variant
from nation.models import Nation
from province.models import Province
from unit.models import Unit
from common.constants import UnitType

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

    game_a_phase_1 = game_a.phases.create(ordinal=1, season="Spring", year=1901, type="Movement")
    game_a_phase_2 = game_a.phases.create(ordinal=2, season="Fall", year=1901, type="Movement")
    game_b_phase_1 = game_b.phases.create(ordinal=1, season="Spring", year=1902, type="Movement")
    game_b_phase_2 = game_b.phases.create(ordinal=2, season="Fall", year=1902, type="Movement")

    # Get actual model instances for classical variant
    england = Nation.objects.get(name="England", variant=variant_a)
    france = Nation.objects.get(name="France", variant=variant_a)
    edi = Province.objects.get(province_id="edi", variant=variant_a)
    lon = Province.objects.get(province_id="lon", variant=variant_a)

    # Get actual model instances for italy-vs-germany variant
    italy = Nation.objects.get(name="Italy", variant=variant_b)
    germany = Nation.objects.get(name="Germany", variant=variant_b)
    rom = Province.objects.get(province_id="rom", variant=variant_b)
    mun = Province.objects.get(province_id="mun", variant=variant_b)

    game_a_phase_1.supply_centers.create(province=edi, nation=england)
    game_a_phase_2.supply_centers.create(province=lon, nation=france)
    game_b_phase_1.supply_centers.create(province=rom, nation=italy)
    game_b_phase_2.supply_centers.create(province=mun, nation=germany)

    game_a_phase_1.units.create(type=UnitType.ARMY, nation=england, province=edi)
    game_a_phase_2.units.create(type=UnitType.ARMY, nation=france, province=lon)
    game_b_phase_1.units.create(type=UnitType.ARMY, nation=italy, province=rom)
    game_b_phase_2.units.create(type=UnitType.ARMY, nation=germany, province=mun)

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

    profile_1 = UserProfile.objects.create(user=user_1, name="User One", picture="http://example.com/1.jpg")
    profile_2 = UserProfile.objects.create(user=user_2, name="User Two", picture="http://example.com/2.jpg")
    profile_3 = UserProfile.objects.create(user=user_3, name="User Three", picture="http://example.com/3.jpg")

    # Get actual nation instances
    england = Nation.objects.get(name="England", variant=variant_a)
    france = Nation.objects.get(name="France", variant=variant_a)
    germany = Nation.objects.get(name="Germany", variant=variant_b)

    game_a.members.create(user=user_1, nation=england)
    game_a.members.create(user=user_2, nation=france)
    game_b.members.create(user=user_3, nation=germany)

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

    # Get actual nation instances
    england = Nation.objects.get(name="England", variant=variant_a)
    france = Nation.objects.get(name="France", variant=variant_a)
    germany = Nation.objects.get(name="Germany", variant=variant_b)

    game_a.members.create(user=user_1, nation=england)
    game_a.members.create(user=user_2, nation=france)
    game_b.members.create(user=user_2, nation=germany)

    connection.queries_log.clear()

    queryset = models.Game.objects.get_queryset().includes_user(user_1)

    with django_assert_num_queries(1):
        games = list(queryset)
        assert len(games) == 1
        assert games[0].name == "Game A"
