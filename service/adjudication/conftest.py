from game.models.game import Game
import pytest
from django.apps import apps
from variant.models import Variant
from nation.models import Nation
from province.models import Province
from unit.models import Unit
from supply_center.models import SupplyCenter
from order.models import Order
from common.constants import OrderType, UnitType
from member.models import Member
from phase.models import Phase


@pytest.fixture(scope="session")
def italy_vs_germany_variant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return Variant.objects.get(id="italy-vs-germany")


@pytest.fixture(scope="session")
def italy_vs_germany_italy_nation(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Italy", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_germany_nation(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Germany", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_venice_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ven", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_rome_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="rom", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_greece_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="gre", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_warsaw_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="war", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_naples_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="nap", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_trieste_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="tri", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_kiel_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="kie", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_berlin_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ber", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_munich_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="mun", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_ionian_sea_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ion", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_denmark_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="den", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_prussia_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="pru", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_ruhr_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ruh", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def game(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Game.objects.create(variant=italy_vs_germany_variant, name="Test Game", status=Game.ACTIVE)


@pytest.fixture(scope="session")
def member_italy(
    django_db_setup, django_db_blocker, italy_vs_germany_variant, italy_vs_germany_italy_nation, primary_user, game
):
    with django_db_blocker.unblock():
        return Member.objects.create(nation=italy_vs_germany_italy_nation, user=primary_user, game=game)


@pytest.fixture(scope="session")
def member_germany(
    django_db_setup, django_db_blocker, italy_vs_germany_variant, italy_vs_germany_germany_nation, secondary_user, game
):
    with django_db_blocker.unblock():
        return Member.objects.create(nation=italy_vs_germany_germany_nation, user=secondary_user, game=game)


@pytest.fixture(scope="function")
def phase_spring_1901_movement(django_db_setup, django_db_blocker, game):
    with django_db_blocker.unblock():
        return Phase.objects.create(
            game=game, variant=game.variant, season="Spring", year=1901, type="Movement", ordinal=1
        )


@pytest.fixture(scope="function")
def phase_spring_1901_retreat(django_db_setup, django_db_blocker, game):
    with django_db_blocker.unblock():
        return Phase.objects.create(
            game=game, variant=game.variant, season="Spring", year=1901, type="Retreat", ordinal=2
        )


@pytest.fixture(scope="function")
def phase_fall_1901_movement(django_db_setup, django_db_blocker, game):
    with django_db_blocker.unblock():
        return Phase.objects.create(
            game=game, variant=game.variant, season="Fall", year=1901, type="Movement", ordinal=3
        )


@pytest.fixture(scope="function")
def phase_fall_1901_retreat(django_db_setup, django_db_blocker, game):
    with django_db_blocker.unblock():
        return Phase.objects.create(
            game=game, variant=game.variant, season="Fall", year=1901, type="Retreat", ordinal=4
        )


@pytest.fixture(scope="function")
def phase_fall_1901_adjustment(django_db_setup, django_db_blocker, game):
    with django_db_blocker.unblock():
        return Phase.objects.create(
            game=game, variant=game.variant, season="Fall", year=1901, type="Adjustment", ordinal=5
        )
